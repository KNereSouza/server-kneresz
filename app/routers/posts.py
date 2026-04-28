from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.dependencies import (
    get_current_user_optional,
    get_db,
    is_admin_user,
    require_admin,
)
from app.models.slug_redirect import SlugRedirect
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.post import PostCreate, PostList, PostOut, PostStatus, PostUpdate, PurgeConfirm
from app.services import posts as posts_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostList)
async def list_posts(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tag: list[str] | None = Query(None),
    status: PostStatus | None = None,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if not is_admin_user(current_user):
        status = PostStatus.published
        include_deleted = False

    items, total = await posts_service.list_posts(
        db,
        offset=offset,
        limit=limit,
        tags=tag,
        status_filter=status.value if status else None,
        include_deleted=include_deleted,
    )
    return PostList(items=items, total=total)


@router.get("/{slug}", response_model=PostOut)
async def get_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    result = await posts_service.get_post_by_slug(db, slug)
    if isinstance(result, SlugRedirect):
        from sqlalchemy import select
        from app.models.post import Post
        post = (await db.execute(
            select(Post).where(Post.id == result.post_id, Post.deleted_at.is_(None))
        )).scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return RedirectResponse(
            url=f"/posts/{post.slug}",
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
        )
    if not is_admin_user(current_user) and result.status != PostStatus.published.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return result


@router.post("", response_model=PostOut, status_code=201)
@limiter.limit("30/minute")
async def create_post(
    request: Request,
    data: PostCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await posts_service.create_post(db, data.model_dump())


@router.put("/{slug}", response_model=PostOut)
@limiter.limit("60/minute")
async def update_post(
    request: Request,
    slug: str,
    data: PostUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await posts_service.update_post(db, slug, data.model_dump(exclude_unset=True))


@router.delete("/{slug}", response_model=PostOut)
async def soft_delete_post(
    slug: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await posts_service.soft_delete_post(db, slug)


@router.post("/{slug}/restore", response_model=PostOut)
async def restore_post(
    slug: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await posts_service.restore_post(db, slug)


@router.delete("/{slug}/purge", status_code=204)
async def purge_post(
    slug: str,
    body: PurgeConfirm,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.confirm != slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation slug does not match",
        )
    await posts_service.purge_post(db, slug)
