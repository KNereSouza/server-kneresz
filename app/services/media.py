import re
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.media import Media
from app.models.post import Post
from app.utils.r2 import get_r2_client

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


async def upload_media(db: AsyncSession, file: UploadFile) -> Media:
    content_type = file.content_type or ""

    if content_type in ALLOWED_IMAGE_TYPES:
        max_size = MAX_IMAGE_SIZE
    elif content_type in ALLOWED_VIDEO_TYPES:
        max_size = MAX_VIDEO_SIZE
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}",
        )

    data = await file.read()
    if len(data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max: {max_size // (1024 * 1024)}MB",
        )

    ext = (file.filename or "").rsplit(".", 1)[-1] if file.filename and "." in file.filename else ""
    key = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

    r2 = get_r2_client()
    url = r2.upload_file(data, content_type, key)

    media = Media(
        url=url,
        filename=file.filename or key,
        content_type=content_type,
        size_bytes=len(data),
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


async def list_media(db: AsyncSession) -> list[Media]:
    result = await db.execute(select(Media).order_by(Media.created_at.desc()))
    return list(result.scalars().all())


async def delete_media(db: AsyncSession, media_id: uuid.UUID) -> None:
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    key = media.url.rsplit("/", 1)[-1]
    r2 = get_r2_client()
    r2.delete_file(key)

    await db.delete(media)
    await db.commit()


async def garbage_collect(db: AsyncSession) -> tuple[int, list[uuid.UUID]]:
    # Gather all URLs referenced in post bodies
    posts_result = await db.execute(select(Post.body))
    referenced_urls: set[str] = set()
    for (body,) in posts_result:
        referenced_urls.update(re.findall(r'https?://\S+', body))

    # Find media not referenced by any post
    all_media = await db.execute(select(Media))
    orphans: list[Media] = []
    for media in all_media.scalars():
        if media.url not in referenced_urls:
            orphans.append(media)

    r2 = get_r2_client()
    deleted_ids: list[uuid.UUID] = []
    for media in orphans:
        key = media.url.rsplit("/", 1)[-1]
        r2.delete_file(key)
        deleted_ids.append(media.id)
        await db.delete(media)

    await db.commit()
    return len(deleted_ids), deleted_ids
