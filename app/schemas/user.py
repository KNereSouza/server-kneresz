import uuid
from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    github_id: int
    github_username: str
    avatar_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
