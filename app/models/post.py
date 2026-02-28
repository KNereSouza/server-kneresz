import uuid

from sqlalchemy import Index, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
    deleted_at = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_posts_tags", "tags", postgresql_using="gin"),
        Index(
            "ix_posts_status_created",
            "status",
            "created_at",
            postgresql_where=deleted_at.is_(None),
        ),
    )
