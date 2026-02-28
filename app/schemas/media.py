import uuid
from datetime import datetime

from pydantic import BaseModel


class MediaOut(BaseModel):
    id: uuid.UUID
    url: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GCResponse(BaseModel):
    deleted_count: int
    deleted_ids: list[uuid.UUID]
