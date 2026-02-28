import uuid
from datetime import datetime

from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class PostUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class PostOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    body: str
    tags: list[str]
    status: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostList(BaseModel):
    items: list[PostOut]
    total: int


class PurgeConfirm(BaseModel):
    confirm: str
