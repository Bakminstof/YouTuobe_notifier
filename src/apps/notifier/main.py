from asyncio import Event, gather, get_running_loop, sleep

from aiogram import Bot

from apps.notifier.models import ChannelModel
from apps.notifier.utils import (
    check_new_content,
    db_load_ch_content,
    load_content_urls,
    save_new_content,
)
from controllers.message_ctrl import send_message
from core.models import Smiles
from core.settings import settings
from database.schemas import Channel, ProfileChannelAssociation
from database.utils import get_channel_db


class Notifier:
    YOUTUBE_BASE_URL: str = "https://www.youtube.com"

    stop_event = Event()
    iter_event = Event()
    starter_event = Event()

    def __init__(self, bot: Bot, iter_delay: int = 300) -> None:
        self.bot = bot
        self.iter_delay = iter_delay

    async def start(self) -> None:
        loop = get_running_loop()
        loop.create_task(self.__starter(self.iter_delay))

        while not self.stop_event.is_set():
            await self.notify()

            self.starter_event.set()
            await self.iter_event.wait()
            self.iter_event.clear()

    def stop(self) -> None:
        self.stop_event.set()
        self.iter_event.set()

    async def __starter(self, iter_delay: int) -> None:
        current = 0

        while not self.stop_event.is_set():
            await self.starter_event.wait()

            if current == iter_delay:
                self.iter_event.set()
                self.starter_event.clear()
                current = 0

            else:
                await sleep(1)
                current += 1

        self.iter_event.set()

    async def notify(self):
        async with get_channel_db() as channel_db:
            async for channels in channel_db.aiter_load(
                channel_db.get, max_pages=None, per_page=10
            ):
                ch_models = self.make_channels_models(channels)

                await db_load_ch_content(ch_models)
                await load_content_urls(ch_models)
                check_new_content(ch_models)
                await save_new_content(ch_models)
                self.build_content_msgs(ch_models)
                await self.send_new_content(ch_models)

    @classmethod
    def make_channels_models(cls, channels: list[Channel]) -> list[ChannelModel]:
        models = []

        for channel in channels:
            ch_model = ChannelModel(
                id=channel.id,
                name=channel.name,
                url=channel.url,
                target_tg_ids=cls._get_target_tg_ids(channel),
            )
            models.append(ch_model)

        return models

    @classmethod
    def _get_target_tg_ids(cls, channel: Channel) -> list[int]:
        tg_ids = []

        for (
            profile_association
        ) in channel.profile_associations:  # type: ProfileChannelAssociation
            tg_ids.append(profile_association.profile.tg_id)

        return tg_ids

    def build_content_msgs(self, channel_models: list[ChannelModel]) -> None:
        for ch_model in channel_models:
            self._build_content_msgs(ch_model)

    def _build_content_msgs(self, ch_model: ChannelModel) -> None:
        messages = []
        content_urls = set()

        content_urls.update(ch_model.new_videos)
        content_urls.update(ch_model.new_streams)

        if content_urls:
            messages.append(self.__build_content_msg(ch_model.name, content_urls))

        ch_model.messages = messages

    def __build_content_msg(self, channel_name: str, content_urls: set[str]) -> str:
        content_msgs = []

        for content_part in content_urls:
            content_url = self.YOUTUBE_BASE_URL + content_part

            content_mes = (
                f"<b><i>{Smiles.orange_play} Смотреть: " f"{content_url}</i></b>"
            )
            content_msgs.append(content_mes)

        content = "\n\n".join(content_msgs)
        return (
            f"{Smiles.blue_ok} <b><i>~ {channel_name} ~"
            "\n\nНовый контент!"
            f"\n\n{content}</i></b>"
        )

    async def send_new_content(self, channel_models: list[ChannelModel]) -> None:
        tasks = []

        for ch_model in channel_models:
            if ch_model.messages:
                tasks.append(self._send_new_content(ch_model))

        await gather(*tasks)

    async def _send_new_content(self, ch_model: ChannelModel) -> None:
        tasks = []

        for msg in ch_model.messages:
            for tg_id in ch_model.target_tg_ids:
                tasks.append(
                    send_message(bot=self.bot, chat_id=tg_id, user_tg_id=tg_id, text=msg)
                )

        await gather(*tasks)
