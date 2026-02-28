from app.services.auth import upsert_user


async def test_upsert_creates_new_user(db):
    github_user = {"id": 12345, "login": "newuser"}
    user = await upsert_user(db, github_user)
    assert user.github_id == 12345
    assert user.github_username == "newuser"
    assert 0 <= user.avatar_id <= 127


async def test_upsert_updates_username(db):
    github_user = {"id": 55555, "login": "original"}
    user1 = await upsert_user(db, github_user)

    github_user["login"] = "updated"
    user2 = await upsert_user(db, github_user)

    assert user2.id == user1.id
    assert user2.github_username == "updated"


async def test_upsert_preserves_avatar_on_update(db):
    github_user = {"id": 77777, "login": "first"}
    user1 = await upsert_user(db, github_user)
    original_avatar = user1.avatar_id

    github_user["login"] = "second"
    user2 = await upsert_user(db, github_user)

    assert user2.avatar_id == original_avatar


async def test_upsert_avatar_in_valid_range(db):
    avatars = []
    for i in range(20):
        user = await upsert_user(db, {"id": 10000 + i, "login": f"user{i}"})
        avatars.append(user.avatar_id)
    assert all(0 <= a <= 127 for a in avatars)
