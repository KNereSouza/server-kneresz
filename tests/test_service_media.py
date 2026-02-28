import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.services.media import (
    delete_media,
    garbage_collect,
    list_media,
    upload_media,
)
from app.services.posts import create_post


def _make_upload_file(
    filename="test.jpg",
    content_type="image/jpeg",
    data=b"fake image data",
):
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type
    file.read = AsyncMock(return_value=data)
    return file


async def test_upload_image(db, mock_r2):
    file = _make_upload_file()
    media = await upload_media(db, file)
    assert media.filename == "test.jpg"
    assert media.content_type == "image/jpeg"
    assert media.size_bytes == len(b"fake image data")
    mock_r2.upload_file.assert_called_once()


async def test_upload_video(db, mock_r2):
    file = _make_upload_file(
        filename="clip.mp4", content_type="video/mp4", data=b"video"
    )
    media = await upload_media(db, file)
    assert media.content_type == "video/mp4"


async def test_upload_unsupported_type(db, mock_r2):
    file = _make_upload_file(
        filename="doc.pdf", content_type="application/pdf"
    )
    with pytest.raises(HTTPException) as exc_info:
        await upload_media(db, file)
    assert exc_info.value.status_code == 400


async def test_upload_oversized_image(db, mock_r2):
    big_data = b"x" * (10 * 1024 * 1024 + 1)
    file = _make_upload_file(data=big_data)
    with pytest.raises(HTTPException) as exc_info:
        await upload_media(db, file)
    assert exc_info.value.status_code == 400


async def test_upload_oversized_video(db, mock_r2):
    big_data = b"x" * (100 * 1024 * 1024 + 1)
    file = _make_upload_file(
        filename="big.mp4", content_type="video/mp4", data=big_data
    )
    with pytest.raises(HTTPException) as exc_info:
        await upload_media(db, file)
    assert exc_info.value.status_code == 400


async def test_list_media(db, mock_r2):
    await upload_media(db, _make_upload_file(filename="a.jpg"))
    await upload_media(db, _make_upload_file(filename="b.jpg"))
    items = await list_media(db)
    assert len(items) == 2


async def test_delete_media(db, mock_r2):
    media = await upload_media(db, _make_upload_file())
    await delete_media(db, media.id)
    items = await list_media(db)
    assert len(items) == 0
    mock_r2.delete_file.assert_called_once()


async def test_garbage_collect(db, mock_r2):
    mock_r2.upload_file.side_effect = [
        "https://r2.example.com/used.jpg",
        "https://r2.example.com/orphan.jpg",
    ]
    media_used = await upload_media(db, _make_upload_file(filename="used.jpg"))
    media_orphan = await upload_media(
        db, _make_upload_file(filename="orphan.jpg")
    )

    await create_post(
        db,
        {
            "title": "Post With Image",
            "body": f"Image: {media_used.url}",
        },
    )

    count, ids = await garbage_collect(db)
    assert count == 1
    assert media_orphan.id in ids
