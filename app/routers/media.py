import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.dependencies import get_db, require_admin
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.media import GCResponse, MediaOut
from app.services import media as media_service

router = APIRouter(tags=["media"])


@router.post("/media", response_model=MediaOut, status_code=201)
@limiter.limit("30/minute")
async def upload_media(
    request: Request,
    file: UploadFile,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await media_service.upload_media(db, file)


@router.get("/media", response_model=list[MediaOut])
async def list_media(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await media_service.list_media(db)


@router.delete("/media/{media_id}", status_code=204)
async def delete_media(
    media_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await media_service.delete_media(db, media_id)


@router.post("/admin/media/gc", response_model=GCResponse)
async def garbage_collect(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    count, ids = await media_service.garbage_collect(db)
    return GCResponse(deleted_count=count, deleted_ids=ids)
