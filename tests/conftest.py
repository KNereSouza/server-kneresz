from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.dependencies import get_db
from app.main import app
from app.models.post import Post
from app.models.user import User
from app.services.auth import create_access_token

# NullPool: each session gets a fresh connection, no reuse across event loops
_test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
_test_session = async_sessionmaker(_test_engine, expire_on_commit=False)

_TRUNCATE = text(
    "TRUNCATE comments, slug_redirects, media, posts, users "
    "RESTART IDENTITY CASCADE"
)


# -- Database ------------------------------------------------------------------


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    async with _test_session() as session:
        yield session
    async with _test_engine.begin() as conn:
        await conn.execute(_TRUNCATE)


@pytest.fixture
def override_get_db(db: AsyncSession):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


# -- Rate limiter reset --------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.routers.comments import limiter

    limiter.reset()
    yield


# -- R2 mock -------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_r2(monkeypatch):
    mock_client = MagicMock()
    mock_client.upload_file.return_value = (
        f"{settings.R2_PUBLIC_URL}/test-key.png"
    )
    mock_client.delete_file.return_value = None
    monkeypatch.setattr("app.utils.r2._r2_client", mock_client)
    yield mock_client


# -- Users & auth --------------------------------------------------------------


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(github_id=99999, github_username="testuser", avatar_id=42)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    u = User(
        github_id=settings.ADMIN_GITHUB_ID,
        github_username="admin",
        avatar_id=0,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
def user_token(user: User) -> str:
    return create_access_token(str(user.id))


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(str(admin_user.id))


@pytest.fixture
def user_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


# -- HTTP client ---------------------------------------------------------------


@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# -- Data factories ------------------------------------------------------------


@pytest.fixture
async def sample_post(db: AsyncSession) -> Post:
    from app.services.posts import create_post

    return await create_post(
        db,
        {
            "title": "Test Post Title",
            "body": "Body with https://example.com/media.png link.",
            "tags": ["python", "testing"],
        },
    )
