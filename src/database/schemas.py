from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins import AuditMixin
from database.tps import str_200
from core.models import Status


class Profile(Base, AuditMixin):
    __tablename__ = "profile"

    repr_cols = ("id", "first_name", "status")

    tg_id: Mapped[int]
    username: Mapped[str_200]
    first_name: Mapped[str_200]
    last_name: Mapped[str_200 | None]
    status: Mapped[Status] = mapped_column(default=Status.active)
    subs_limit: Mapped[int] = mapped_column(default=6)
    auth_timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    # =============================|Channels relationship|============================== #
    channel_associations: Mapped[list[ProfileChannelAssociation]] = relationship(
        back_populates="profile"
    )


class Channel(Base, AuditMixin):
    __tablename__ = "channel"

    repr_cols = ("name", "url")

    name: Mapped[str_200]
    url: Mapped[str_200]
    canonical_url: Mapped[str_200]

    # =============================|Profiles relationship|============================== #
    profile_associations: Mapped[list[ProfileChannelAssociation]] = relationship(
        back_populates="channel"
    )

    # ===============================|Video relationship|=============================== #
    videos: Mapped[list[Video]] = relationship(back_populates="channel")

    # ==============================|Stream relationship|=============================== #
    streams: Mapped[list[Stream]] = relationship(back_populates="channel")


class ProfileChannelAssociation(Base, AuditMixin):
    __tablename__ = "profile_channel_association"

    repr_cols = ("id", "profile_id", "channel_id")

    # ==============================|Profile relationship|============================== #
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profile.id"),
    )
    profile: Mapped[Profile] = relationship(back_populates="channel_associations")

    # ==============================|Channel relationship|============================== #
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channel.id"),
    )
    channel: Mapped[Channel] = relationship(back_populates="profile_associations")

    # ===================================|Table args|=================================== #
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "channel_id",
            name=f"{__tablename__}__profile_id_channel_id__uc",
        ),
    )


class Video(Base, AuditMixin):
    __tablename__ = "video"

    repr_cols = ("id", "url")

    url: Mapped[str_200]

    # ==============================|Channel relationship|============================== #
    channel_id: Mapped[int] = mapped_column(ForeignKey("channel.id"))
    channel: Mapped[Channel] = relationship(back_populates="videos")


class Stream(Base, AuditMixin):
    __tablename__ = "stream"

    repr_cols = ("id", "url")

    url: Mapped[str_200] = mapped_column(unique=True)

    # ==============================|Channel relationship|============================== #
    channel_id: Mapped[int] = mapped_column(ForeignKey("channel.id"))
    channel: Mapped[Channel] = relationship(back_populates="streams")
