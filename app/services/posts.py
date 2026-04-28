import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.post import Post
from app.models.slug_redirect import SlugRedirect
from app.services.sanitizer import sanitize_markdown
from app.utils.slug import generate_slug


async def list_posts(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    tags: list[str] | None = None,
    status_filter: str | None = None,
    include_deleted: bool = False,
) -> tuple[list[Post], int]:
    query = select(Post)
    count_query = select(func.count()).select_from(Post)

    if not include_deleted:
        query = query.where(Post.deleted_at.is_(None))
        count_query = count_query.where(Post.deleted_at.is_(None))

    if tags:
        query = query.where(Post.tags.overlap(tags))
        count_query = count_query.where(Post.tags.overlap(tags))

    if status_filter:
        query = query.where(Post.status == status_filter)
        count_query = count_query.where(Post.status == status_filter)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Post.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_post_by_slug(db: AsyncSession, slug: str) -> Post | SlugRedirect:
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.deleted_at.is_(None))
    )
    post = result.scalar_one_or_none()
    if post:
        return post

    redirect = await db.execute(
        select(SlugRedirect).where(SlugRedirect.old_slug == slug)
    )
    redirect = redirect.scalar_one_or_none()
    if redirect:
        return redirect

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


async def create_post(db: AsyncSession, data: dict) -> Post:
    slug = generate_slug(data["title"])
    body = sanitize_markdown(data["body"])

    post = Post(
        title=data["title"],
        slug=slug,
        body=body,
        tags=data.get("tags", []),
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def update_post(db: AsyncSession, slug: str, data: dict) -> Post:
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.deleted_at.is_(None))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if data.get("title") and data["title"] != post.title:
        old_slug = post.slug
        new_slug = generate_slug(data["title"])
        post.slug = new_slug
        post.title = data["title"]

        redirect = SlugRedirect(old_slug=old_slug, post_id=post.id)
        db.add(redirect)

    if data.get("body") is not None:
        post.body = sanitize_markdown(data["body"])

    if data.get("tags") is not None:
        post.tags = data["tags"]

    if data.get("status") is not None:
        post.status = data["status"]

    await db.commit()
    await db.refresh(post)
    return post


async def soft_delete_post(db: AsyncSession, slug: str) -> Post:
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.deleted_at.is_(None))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    post.deleted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(post)
    return post


async def restore_post(db: AsyncSession, slug: str) -> Post:
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.deleted_at.is_not(None))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    post.deleted_at = None
    await db.commit()
    await db.refresh(post)
    return post


async def purge_post(db: AsyncSession, slug: str) -> None:
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Find media URLs referenced in the post body
    from app.utils.r2 import get_r2_client
    media_urls = set(re.findall(r'https?://[^\s<>"\'()]+', post.body))
    media_result = await db.execute(
        select(Media).where(Media.url.in_(media_urls))
    )
    media_to_delete = media_result.scalars().all()

    r2 = get_r2_client()
    for media in media_to_delete:
        key = media.url.rsplit("/", 1)[-1]
        r2.delete_file(key)
        await db.delete(media)

    await db.delete(post)
    await db.commit()
