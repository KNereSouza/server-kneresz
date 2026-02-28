from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    exchange_github_code,
    upsert_user,
    verify_token,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github")
async def github_login():
    params = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "read:user",
    })
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        github_user = await exchange_github_code(code)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub OAuth failed")

    user = await upsert_user(db, github_user)
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = verify_token(body.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user
