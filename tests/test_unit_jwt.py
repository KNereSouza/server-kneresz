from datetime import UTC, datetime, timedelta

from jose import jwt

from app.config import settings
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
)


def test_create_and_verify_access_token():
    user_id = "abc-123"
    token = create_access_token(user_id)
    assert verify_token(token) == user_id


def test_create_and_verify_refresh_token():
    user_id = "abc-123"
    token = create_refresh_token(user_id)
    assert verify_token(token, expected_type="refresh") == user_id


def test_access_token_rejected_as_refresh():
    token = create_access_token("user-1")
    assert verify_token(token, expected_type="refresh") is None


def test_refresh_token_rejected_as_access():
    token = create_refresh_token("user-1")
    assert verify_token(token, expected_type="access") is None


def test_verify_expired_token():
    expired = jwt.encode(
        {
            "sub": "user-1",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "type": "access",
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert verify_token(expired) is None


def test_verify_invalid_token():
    assert verify_token("not.a.real.token") is None


def test_verify_token_wrong_secret():
    token = jwt.encode(
        {
            "sub": "user-1",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "access",
        },
        "wrong-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    assert verify_token(token) is None
