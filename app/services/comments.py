import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.models.comment import Comment
from app.models.post import Post
from app.services.sanitizer import sanitize_markdown


async def _get_post_by_slug(db: AsyncSession, slug: str) -> Post:
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.deleted_at.is_(None))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


async def list_comments(db: AsyncSession, slug: str) -> list[Comment]:
    post = await _get_post_by_slug(db, slug)
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.post_id == post.id, Comment.deleted_at.is_(None))
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


async def create_comment(
    db: AsyncSession, slug: str, user_id: uuid.UUID, body: str
) -> Comment:
    post = await _get_post_by_slug(db, slug)

    comment = Comment(
        post_id=post.id,
        user_id=user_id,
        body=sanitize_markdown(body),
    )
    db.add(comment)
    await db.commit()
    result = await db.execute(
        select(Comment).options(joinedload(Comment.user)).where(Comment.id == comment.id)
    )
    return result.scalar_one()


async def soft_delete_comment(
    db: AsyncSession, comment_id: uuid.UUID, user_id: uuid.UUID, is_admin: bool
) -> Comment:
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.id == comment_id, Comment.deleted_at.is_(None))
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if comment.user_id != user_id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    comment.deleted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(comment, attribute_names=["deleted_at"])
    return comment


async def restore_comment(db: AsyncSession, comment_id: uuid.UUID) -> Comment:
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.id == comment_id, Comment.deleted_at.is_not(None))
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    comment.deleted_at = None
    await db.commit()
    await db.refresh(comment, attribute_names=["deleted_at"])
    return comment


async def purge_comment(db: AsyncSession, comment_id: uuid.UUID) -> None:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    await db.delete(comment)
    await db.commit()
