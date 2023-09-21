from dataclasses import dataclass, field
from typing import List

from models.schemas import Channel


@dataclass
class ChannelModel:
    channel: Channel

    users_tg_ids: List[int] = field(default_factory=lambda: [])

    video_content: str | None = None
    stream_content: str | None = None

    new_content: List[str] = field(default_factory=lambda: [])

    update: bool = False
