import uuid

import pytest
from fastapi import HTTPException

from app.services.comments import (
    create_comment,
    list_comments,
    purge_comment,
    restore_comment,
    soft_delete_comment,
)
from app.services.posts import create_post


async def test_create_comment(db, user):
    post = await create_post(db, {"title": "Commented", "body": "Body"})
    comment = await create_comment(db, post.slug, user.id, "Nice post!")
    assert comment.body == "Nice post!"
    assert comment.post_id == post.id
    assert comment.user_id == user.id


async def test_create_comment_sanitizes_body(db, user):
    post = await create_post(db, {"title": "Sanitize", "body": "Body"})
    comment = await create_comment(
        db, post.slug, user.id, '<p>ok</p><script>bad</script>'
    )
    assert "<script>" not in comment.body
    assert "<p>ok</p>" in comment.body


async def test_list_comments_empty(db):
    post = await create_post(db, {"title": "No Comments", "body": "Body"})
    comments = await list_comments(db, post.slug)
    assert comments == []


async def test_list_comments_excludes_deleted(db, user):
    post = await create_post(db, {"title": "Del Comment", "body": "Body"})
    c1 = await create_comment(db, post.slug, user.id, "Keep")
    c2 = await create_comment(db, post.slug, user.id, "Delete")
    await soft_delete_comment(db, c2.id, user.id, is_admin=False)

    comments = await list_comments(db, post.slug)
    assert len(comments) == 1
    assert comments[0].id == c1.id


async def test_list_comments_ordered_by_created_at(db, user):
    post = await create_post(db, {"title": "Ordered", "body": "Body"})
    await create_comment(db, post.slug, user.id, "First")
    await create_comment(db, post.slug, user.id, "Second")
    await create_comment(db, post.slug, user.id, "Third")

    comments = await list_comments(db, post.slug)
    assert [c.body for c in comments] == ["First", "Second", "Third"]


async def test_list_comments_post_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        await list_comments(db, "nonexistent")
    assert exc_info.value.status_code == 404


async def test_soft_delete_by_author(db, user):
    post = await create_post(db, {"title": "Author Del", "body": "Body"})
    comment = await create_comment(db, post.slug, user.id, "My comment")
    deleted = await soft_delete_comment(db, comment.id, user.id, is_admin=False)
    assert deleted.deleted_at is not None


async def test_soft_delete_by_admin(db, user, admin_user):
    post = await create_post(db, {"title": "Admin Del", "body": "Body"})
    comment = await create_comment(db, post.slug, user.id, "User comment")
    deleted = await soft_delete_comment(
        db, comment.id, admin_user.id, is_admin=True
    )
    assert deleted.deleted_at is not None


async def test_soft_delete_forbidden(db, user):
    post = await create_post(db, {"title": "Forbidden", "body": "Body"})
    comment = await create_comment(db, post.slug, user.id, "Not yours")

    other_user_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await soft_delete_comment(
            db, comment.id, other_user_id, is_admin=False
        )
    assert exc_info.value.status_code == 403
