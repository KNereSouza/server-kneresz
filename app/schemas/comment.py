import uuid
from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    user_id: uuid.UUID
    body: str
    deleted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
