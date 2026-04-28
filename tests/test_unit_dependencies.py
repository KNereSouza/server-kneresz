import uuid

from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.dependencies import get_current_user_optional, is_admin_user
from app.models.user import User
from app.services.auth import create_access_token


def _make_user(github_id: int) -> User:
    return User(github_id=github_id, github_username="x", avatar_id=0)


def test_is_admin_user_none():
    assert is_admin_user(None) is False


def test_is_admin_user_regular():
    assert is_admin_user(_make_user(1)) is False


def test_is_admin_user_admin():
    assert is_admin_user(_make_user(settings.ADMIN_GITHUB_ID)) is True


async def test_optional_no_credentials_returns_none(db):
    result = await get_current_user_optional(credentials=None, db=db)
    assert result is None


async def test_optional_invalid_token_returns_none(db):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt")
    result = await get_current_user_optional(credentials=creds, db=db)
    assert result is None


async def test_optional_unknown_user_returns_none(db):
    token = create_access_token(str(uuid.uuid4()))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = await get_current_user_optional(credentials=creds, db=db)
    assert result is None


async def test_optional_valid_user_returns_user(db, user):
    token = create_access_token(str(user.id))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = await get_current_user_optional(credentials=creds, db=db)
    assert result is not None
    assert result.id == user.id
