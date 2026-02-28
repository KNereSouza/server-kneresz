from app.services.auth import create_refresh_token


async def test_github_login_redirects(client):
    resp = await client.get("/auth/github", follow_redirects=False)
    assert resp.status_code == 307
    assert "github.com/login/oauth/authorize" in resp.headers["location"]


async def test_github_callback_success(client, monkeypatch):
    async def mock_exchange(code: str) -> dict:
        return {"id": 12345, "login": "ghuser"}

    monkeypatch.setattr(
        "app.routers.auth.exchange_github_code", mock_exchange
    )
    resp = await client.get("/auth/github/callback", params={"code": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_github_callback_failure(client, monkeypatch):
    async def mock_exchange(code: str) -> dict:
        raise Exception("OAuth failed")

    monkeypatch.setattr(
        "app.routers.auth.exchange_github_code", mock_exchange
    )
    resp = await client.get("/auth/github/callback", params={"code": "bad"})
    assert resp.status_code == 400


async def test_refresh_token_success(client, user):
    refresh = create_refresh_token(str(user.id))
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": refresh}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_fails(client, user_token):
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": user_token}
    )
    assert resp.status_code == 401


async def test_refresh_with_invalid_token(client):
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": "garbage"}
    )
    assert resp.status_code == 401


async def test_get_me_authenticated(client, user_headers):
    resp = await client.get("/auth/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["github_username"] == "testuser"


async def test_get_me_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
