from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy import (
    BOOLEAN,
    SMALLINT,
    ForeignKey,
    String,
    UniqueConstraint,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def to_dict(
        self,
        only: List[str] | Tuple[str, ...] | None = None,
        exclude: List[str] | Tuple[str, ...] | None = None,
    ) -> Dict[str, Any]:
        item = {}

        for column in self.__table__.columns:  # noqa
            if column.key in self.__dict__:
                if only:
                    if column.key in only:
                        item[column.key] = getattr(self, column.key)
                    continue

                if exclude:
                    if column.key not in exclude:
                        item[column.key] = getattr(self, column.key)
                    continue

                item[column.key] = getattr(self, column.key)

        return item


class Association(Base):
    __tablename__ = "association"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel_id",
            name="_user_channel_uc",
        ),
    )

    id: Mapped[int] = mapped_column(
        "id",
        BIGINT,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="channels", lazy="joined")
    channel: Mapped["Channel"] = relationship(back_populates="users", lazy="joined")


class User(Base):
    default_subs_count: int = 10

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        "id",
        BIGINT,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        "telegram_id",
        BIGINT,
        nullable=False,
        unique=True,
    )
    first_name: Mapped[str] = mapped_column(
        "first_name",
        String(200),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        "last_name",
        String(200),
        nullable=True,
    )
    add_subs_count: Mapped[int] = mapped_column(
        "add_subs_count",
        SMALLINT,
        nullable=False,
        default=0,
    )
    auth_timestamp: Mapped[datetime] = mapped_column(
        "auth_timestamp",
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
    )
    blocked: Mapped[bool] = mapped_column(
        "blocked",
        BOOLEAN,
        default=False,
        nullable=False,
        index=True,
    )

    # Channels relationship
    channels: Mapped[List[Association]] = relationship(
        back_populates="user",
        lazy="joined",
    )


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(
        "id",
        BIGINT,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        "name",
        String(200),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        "url",
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )
    canonical_url: Mapped[str] = mapped_column(
        "canonical_url",
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )
    last_videos: Mapped[List[str]] = mapped_column(
        "last_videos",
        ARRAY(String),
        nullable=False,
        default=[],
    )
    last_streams: Mapped[List[str]] = mapped_column(
        "last_streams",
        ARRAY(String),
        nullable=False,
        default=[],
    )

    # Users relationship
    users: Mapped[List[Association]] = relationship(
        back_populates="channel",
        lazy="joined",
    )


class Temp(Base):
    __tablename__ = "temp"

    id: Mapped[int] = mapped_column(
        "id",
        BIGINT,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        "telegram_id",
        BIGINT,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        "text",
        String(4096),
        nullable=True,
    )
