async def test_list_posts_empty(client):
    resp = await client.get("/posts")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


async def test_list_posts_with_data(client, admin_headers):
    await client.post(
        "/posts",
        json={"title": "Post A", "body": "A"},
        headers=admin_headers,
    )
    await client.post(
        "/posts",
        json={"title": "Post B", "body": "B"},
        headers=admin_headers,
    )
    resp = await client.get("/posts")
    assert resp.json()["total"] == 2


async def test_list_posts_pagination(client, admin_headers):
    for i in range(3):
        await client.post(
            "/posts",
            json={"title": f"Page {i}", "body": "X"},
            headers=admin_headers,
        )
    resp = await client.get("/posts?offset=0&limit=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


async def test_list_posts_filter_by_tag(client, admin_headers):
    await client.post(
        "/posts",
        json={"title": "Rust Post", "body": "X", "tags": ["rust"]},
        headers=admin_headers,
    )
    await client.post(
        "/posts",
        json={"title": "Python Post", "body": "X", "tags": ["python"]},
        headers=admin_headers,
    )
    resp = await client.get("/posts?tag=rust")
    assert resp.json()["total"] == 1


async def test_list_posts_filter_by_status(client, admin_headers):
    create_resp = await client.post(
        "/posts",
        json={"title": "Publish Me", "body": "X"},
        headers=admin_headers,
    )
    slug = create_resp.json()["slug"]
    await client.put(
        f"/posts/{slug}",
        json={"status": "published"},
        headers=admin_headers,
    )
    await client.post(
        "/posts",
        json={"title": "Stay Draft", "body": "X"},
        headers=admin_headers,
    )
    resp = await client.get("/posts?status=published")
    assert resp.json()["total"] == 1


async def test_get_post_by_slug(client, sample_post):
    resp = await client.get(f"/posts/{sample_post.slug}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Post Title"


async def test_get_post_not_found(client):
    resp = await client.get("/posts/nonexistent")
    assert resp.status_code == 404


async def test_get_post_slug_redirect(client, admin_headers):
    create_resp = await client.post(
        "/posts",
        json={"title": "Redirect Original", "body": "X"},
        headers=admin_headers,
    )
    old_slug = create_resp.json()["slug"]
    await client.put(
        f"/posts/{old_slug}",
        json={"title": "Redirect New"},
        headers=admin_headers,
    )
    resp = await client.get(f"/posts/{old_slug}", follow_redirects=False)
    assert resp.status_code == 301
    assert "/posts/redirect-new" in resp.headers["location"]


async def test_create_post_as_admin(client, admin_headers):
    resp = await client.post(
        "/posts",
        json={"title": "Admin Post", "body": "Content", "tags": ["api"]},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "admin-post"
    assert data["tags"] == ["api"]


async def test_create_post_as_user_forbidden(client, user_headers):
    resp = await client.post(
        "/posts",
        json={"title": "Nope", "body": "X"},
        headers=user_headers,
    )
    assert resp.status_code == 403


async def test_create_post_unauthenticated(client):
    resp = await client.post(
        "/posts", json={"title": "Nope", "body": "X"}
    )
    assert resp.status_code == 401


async def test_update_post_as_admin(client, admin_headers, sample_post):
    resp = await client.put(
        f"/posts/{sample_post.slug}",
        json={"body": "Updated body"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["body"] == "Updated body"


async def test_soft_delete_post(client, admin_headers, sample_post):
    resp = await client.delete(
        f"/posts/{sample_post.slug}", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is not None


async def test_restore_post(client, admin_headers):
    create_resp = await client.post(
        "/posts",
        json={"title": "Restore Me", "body": "X"},
        headers=admin_headers,
    )
    slug = create_resp.json()["slug"]
    await client.delete(f"/posts/{slug}", headers=admin_headers)

    resp = await client.post(f"/posts/{slug}/restore", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is None


async def test_purge_post(client, admin_headers):
    create_resp = await client.post(
        "/posts",
        json={"title": "Purge Me", "body": "X"},
        headers=admin_headers,
    )
    slug = create_resp.json()["slug"]
    resp = await client.request(
        "DELETE",
        f"/posts/{slug}/purge",
        json={"confirm": slug},
        headers=admin_headers,
    )
    assert resp.status_code == 204


async def test_purge_post_wrong_confirmation(client, admin_headers, sample_post):
    resp = await client.request(
        "DELETE",
        f"/posts/{sample_post.slug}/purge",
        json={"confirm": "wrong"},
        headers=admin_headers,
    )
    assert resp.status_code == 400
