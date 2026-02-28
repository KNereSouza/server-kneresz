import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, model_validator


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    user_id: uuid.UUID
    github_username: str
    avatar_id: int
    body: str
    deleted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def flatten_user(cls, data: Any) -> Any:
        if hasattr(data, "user") and data.user is not None:
            user = data.user
            data.github_username = user.github_username
            data.avatar_id = user.avatar_id
        return data
