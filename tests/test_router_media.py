async def test_upload_as_admin(client, admin_headers):
    resp = await client.post(
        "/media",
        files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["filename"] == "test.jpg"


async def test_upload_as_user_forbidden(client, user_headers):
    resp = await client.post(
        "/media",
        files={"file": ("test.jpg", b"data", "image/jpeg")},
        headers=user_headers,
    )
    assert resp.status_code == 403


async def test_upload_unsupported_type(client, admin_headers):
    resp = await client.post(
        "/media",
        files={"file": ("doc.pdf", b"data", "application/pdf")},
        headers=admin_headers,
    )
    assert resp.status_code == 400


async def test_list_media_as_admin(client, admin_headers):
    await client.post(
        "/media",
        files={"file": ("a.jpg", b"data1", "image/jpeg")},
        headers=admin_headers,
    )
    await client.post(
        "/media",
        files={"file": ("b.png", b"data2", "image/png")},
        headers=admin_headers,
    )
    resp = await client.get("/media", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_media_as_user_forbidden(client, user_headers):
    resp = await client.get("/media", headers=user_headers)
    assert resp.status_code == 403


async def test_delete_media_as_admin(client, admin_headers):
    create_resp = await client.post(
        "/media",
        files={"file": ("del.jpg", b"data", "image/jpeg")},
        headers=admin_headers,
    )
    media_id = create_resp.json()["id"]
    resp = await client.delete(f"/media/{media_id}", headers=admin_headers)
    assert resp.status_code == 204


async def test_gc_as_admin(client, admin_headers):
    resp = await client.post("/admin/media/gc", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "deleted_count" in data
    assert "deleted_ids" in data


async def test_gc_as_user_forbidden(client, user_headers):
    resp = await client.post("/admin/media/gc", headers=user_headers)
    assert resp.status_code == 403
