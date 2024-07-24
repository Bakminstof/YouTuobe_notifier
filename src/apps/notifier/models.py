from enum import StrEnum, auto

from aiogram.types import Message
from pydantic import BaseModel, ConfigDict

from database.schemas import Channel, Profile


class UserFSMmodel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    profile: Profile
    channels: list[Channel] = []
    displayed_channels: dict[int, tuple[Message, Channel]] = {}


class ContentType(StrEnum):
    videos = auto()
    streams = auto()


class ChannelModel(BaseModel):
    id: int
    name: str
    url: str

    target_tg_ids: list[int]
    messages: list[str] = []

    db_videos: list[str] = []
    db_streams: list[str] = []

    loaded_videos: set[str] = set()
    loaded_streams: set[str] = set()

    new_videos: list[str] = []
    new_streams: list[str] = []
