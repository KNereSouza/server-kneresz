import uuid

from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config import settings
from app.dependencies import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut
from app.services import comments as comments_service

router = APIRouter(tags=["comments"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/posts/{slug}/comments", response_model=list[CommentOut])
async def list_comments(slug: str, db: AsyncSession = Depends(get_db)):
    return await comments_service.list_comments(db, slug)


@router.post(
    "/posts/{slug}/comments",
    response_model=CommentOut,
    status_code=201,
)
@limiter.limit("8/minute")
async def create_comment(
    request: Request,
    slug: str,
    data: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await comments_service.create_comment(db, slug, user.id, data.body)


@router.delete("/comments/{comment_id}", response_model=CommentOut)
async def soft_delete_comment(
    comment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = user.github_id == settings.ADMIN_GITHUB_ID
    return await comments_service.soft_delete_comment(db, comment_id, user.id, is_admin)


@router.post("/comments/{comment_id}/restore", response_model=CommentOut)
async def restore_comment(
    comment_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await comments_service.restore_comment(db, comment_id)


@router.delete("/comments/{comment_id}/purge", status_code=204)
async def purge_comment(
    comment_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await comments_service.purge_comment(db, comment_id)
