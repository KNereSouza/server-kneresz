import pytest
from fastapi import HTTPException

from app.models.slug_redirect import SlugRedirect
from app.services.posts import (
    create_post,
    get_post_by_slug,
    list_posts,
    purge_post,
    restore_post,
    soft_delete_post,
    update_post,
)


async def test_create_post(db):
    post = await create_post(
        db, {"title": "My First Post", "body": "Hello", "tags": ["test"]}
    )
    assert post.title == "My First Post"
    assert post.slug == "my-first-post"
    assert post.tags == ["test"]
    assert post.status == "draft"


async def test_create_post_sanitizes_body(db):
    post = await create_post(
        db,
        {"title": "XSS Test", "body": '<p>safe</p><script>alert(1)</script>'},
    )
    assert "<script>" not in post.body
    assert "<p>safe</p>" in post.body


async def test_list_posts_empty(db):
    items, total = await list_posts(db)
    assert items == []
    assert total == 0


async def test_list_posts_excludes_deleted(db):
    await create_post(db, {"title": "Keep", "body": "A"})
    p2 = await create_post(db, {"title": "Delete", "body": "B"})
    await soft_delete_post(db, p2.slug)

    items, total = await list_posts(db)
    assert total == 1
    assert items[0].title == "Keep"


async def test_list_posts_pagination(db):
    for i in range(5):
        await create_post(db, {"title": f"Post {i}", "body": "X"})

    items, total = await list_posts(db, offset=0, limit=2)
    assert len(items) == 2
    assert total == 5

    items2, _ = await list_posts(db, offset=4, limit=2)
    assert len(items2) == 1


async def test_list_posts_filter_by_tag(db):
    await create_post(db, {"title": "Python Post", "body": "A", "tags": ["python"]})
    await create_post(db, {"title": "Rust Post", "body": "B", "tags": ["rust"]})
    await create_post(
        db, {"title": "Both", "body": "C", "tags": ["python", "rust"]}
    )

    items, total = await list_posts(db, tag="python")
    assert total == 2

    items, total = await list_posts(db, tag="rust")
    assert total == 2


async def test_list_posts_filter_by_status(db):
    p = await create_post(db, {"title": "Draft", "body": "A"})
    await create_post(db, {"title": "Also Draft", "body": "B"})
    await update_post(db, p.slug, {"status": "published"})

    items, total = await list_posts(db, status_filter="published")
    assert total == 1
    assert items[0].title == "Draft"


async def test_get_post_by_slug_found(db):
    created = await create_post(db, {"title": "Find Me", "body": "Body"})
    found = await get_post_by_slug(db, "find-me")
    assert found.id == created.id


async def test_get_post_by_slug_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        await get_post_by_slug(db, "nonexistent")
    assert exc_info.value.status_code == 404


async def test_get_post_by_slug_redirect(db):
    post = await create_post(db, {"title": "Original", "body": "Body"})
    await update_post(db, "original", {"title": "Updated Title"})

    result = await get_post_by_slug(db, "original")
    assert isinstance(result, SlugRedirect)
    assert result.post_id == post.id


async def test_update_post_title_creates_redirect(db):
    await create_post(db, {"title": "Old Title", "body": "Body"})
    updated = await update_post(db, "old-title", {"title": "New Title"})
    assert updated.slug == "new-title"
    assert updated.title == "New Title"

    result = await get_post_by_slug(db, "old-title")
    assert isinstance(result, SlugRedirect)


async def test_update_post_partial_fields(db):
    post = await create_post(
        db, {"title": "Keep Title", "body": "Old body", "tags": ["a"]}
    )
    updated = await update_post(db, post.slug, {"body": "New body"})
    assert updated.title == "Keep Title"
    assert updated.body == "New body"
    assert updated.tags == ["a"]


async def test_soft_delete_and_restore(db):
    post = await create_post(db, {"title": "Lifecycle", "body": "Body"})

    deleted = await soft_delete_post(db, post.slug)
    assert deleted.deleted_at is not None

    restored = await restore_post(db, post.slug)
    assert restored.deleted_at is None


async def test_purge_post(db, mock_r2):
    post = await create_post(db, {"title": "To Purge", "body": "Body"})
    await purge_post(db, post.slug)

    with pytest.raises(HTTPException) as exc_info:
        await get_post_by_slug(db, "to-purge")
    assert exc_info.value.status_code == 404
