async def test_list_comments_empty(client, sample_post):
    resp = await client.get(f"/posts/{sample_post.slug}/comments")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_comments_with_data(client, sample_post, user_headers):
    await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Comment 1"},
        headers=user_headers,
    )
    await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Comment 2"},
        headers=user_headers,
    )
    resp = await client.get(f"/posts/{sample_post.slug}/comments")
    assert len(resp.json()) == 2


async def test_create_comment_as_user(client, sample_post, user_headers):
    resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Great post!"},
        headers=user_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["body"] == "Great post!"


async def test_create_comment_unauthenticated(client, sample_post):
    resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "No auth"},
    )
    assert resp.status_code == 401


async def test_create_comment_post_not_found(client, user_headers):
    resp = await client.post(
        "/posts/nonexistent/comments",
        json={"body": "Hello"},
        headers=user_headers,
    )
    assert resp.status_code == 404


async def test_soft_delete_own_comment(client, sample_post, user_headers):
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Delete me"},
        headers=user_headers,
    )
    comment_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/comments/{comment_id}", headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is not None


async def test_soft_delete_others_forbidden(
    client, sample_post, user_headers, admin_headers
):
    # Admin creates a comment
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Admin's comment"},
        headers=admin_headers,
    )
    comment_id = create_resp.json()["id"]

    # Regular user tries to delete it
    resp = await client.delete(
        f"/comments/{comment_id}", headers=user_headers
    )
    assert resp.status_code == 403


async def test_admin_can_delete_any_comment(
    client, sample_post, user_headers, admin_headers
):
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "User's comment"},
        headers=user_headers,
    )
    comment_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/comments/{comment_id}", headers=admin_headers
    )
    assert resp.status_code == 200


async def test_restore_comment_as_admin(
    client, sample_post, user_headers, admin_headers
):
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Restore me"},
        headers=user_headers,
    )
    comment_id = create_resp.json()["id"]
    await client.delete(f"/comments/{comment_id}", headers=user_headers)

    resp = await client.post(
        f"/comments/{comment_id}/restore", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["deleted_at"] is None


async def test_restore_comment_as_user_forbidden(
    client, sample_post, user_headers
):
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "No restore for you"},
        headers=user_headers,
    )
    comment_id = create_resp.json()["id"]
    await client.delete(f"/comments/{comment_id}", headers=user_headers)

    resp = await client.post(
        f"/comments/{comment_id}/restore", headers=user_headers
    )
    assert resp.status_code == 403


async def test_purge_comment_as_admin(
    client, sample_post, user_headers, admin_headers
):
    create_resp = await client.post(
        f"/posts/{sample_post.slug}/comments",
        json={"body": "Purge me"},
        headers=user_headers,
    )
    comment_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/comments/{comment_id}/purge", headers=admin_headers
    )
    assert resp.status_code == 204
