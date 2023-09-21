from contextlib import AbstractAsyncContextManager
from logging import Logger, getLogger
from re import search
from typing import Callable, Dict, List, Sequence, Tuple

from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from controllers import MessageController
from keyboards.inline import unsub_keyboard
from models.managers import AssociationManager, ChannelManager, get_session
from models.models import ChannelModel
from models.schemas import Association, Channel, User
from settings import settings
from utils.common import limit_gather
from utils.finder import Finder
from utils.http import HTTPManager


class ChannelController:
    logger: Logger = getLogger(__name__)

    CONTENT_ARRAY_MAX_LEN: int = 60
    YOUTUBE_BASE_URL: str = "https://www.youtube.com"

    def __init__(self) -> None:
        self.get_session: Callable[
            [None],
            AbstractAsyncContextManager[AsyncSession],
        ] = get_session  # type: ignore

        self.message_controller: MessageController = MessageController()

        self.association_manager: AssociationManager = AssociationManager()
        self.channel_manager: ChannelManager = ChannelManager()
        self.http_manager: HTTPManager = HTTPManager()

        self.models_data: List[ChannelModel] = []
        self.finder: Finder = Finder()

    async def load_from_db(self) -> None:
        async with self.get_session() as async_session:
            channels = await self.channel_manager.get_channels_with_users(async_session)

        data: List[ChannelModel] = []

        for channel in channels:
            users_tg_ids = [association.user.telegram_id for association in channel.users]
            data.append(ChannelModel(channel, users_tg_ids=users_tg_ids))

        self.models_data = data

    async def get_content(self, models_data: List[ChannelModel]) -> None:
        content_tasks = []

        for ch_model in models_data:
            for content_type, url_suffix in (
                ("video", "/videos"),
                ("stream", "/streams"),
            ):
                url = ch_model.channel.canonical_url + url_suffix
                content_tasks.append(self.__get_content(ch_model, url, content_type))

        await limit_gather(content_tasks, 30, 2)

    async def __get_content(
        self,
        ch_model: ChannelModel,
        url: str,
        content_type: str,
    ) -> None:
        response = await self.http_manager.get(url)
        text_or_none = response.text if response else None

        if content_type == "video":
            ch_model.video_content = text_or_none

        elif content_type == "stream":
            ch_model.stream_content = text_or_none

    def analise_found_content(self, models_data: List[ChannelModel]) -> None:
        for ch_model in models_data:
            for content_type in ("video", "stream"):
                self.__check_new_content(ch_model, content_type)

    def __set_last_content(
        self,
        ch_model: ChannelModel,
        last_content_atr_name: str,
        new_content: List[str],
    ) -> None:
        last_content: List[str] = getattr(ch_model.channel, last_content_atr_name)

        content = new_content + last_content

        if len(content) > self.CONTENT_ARRAY_MAX_LEN:
            content = content[: self.CONTENT_ARRAY_MAX_LEN]

        setattr(ch_model.channel, last_content_atr_name, content)

    def __check_new_content(
        self,
        ch_model: ChannelModel,
        content_type: str,
    ) -> None:
        if content_type == "video":
            text = ch_model.video_content
            last_content_atr_name = "last_videos"

        elif content_type == "stream":
            text = ch_model.stream_content
            last_content_atr_name = "last_streams"

        else:
            return

        found_content = self.finder.find_content_urls(text, ch_model.channel.url)

        if len(found_content) > self.CONTENT_ARRAY_MAX_LEN:
            found_content = found_content[: self.CONTENT_ARRAY_MAX_LEN]

        last_content = getattr(ch_model.channel, last_content_atr_name)
        new_content = []

        for item in found_content:
            if item not in last_content:
                new_content.append(item)

        if new_content:
            self.__set_last_content(ch_model, last_content_atr_name, new_content)
            ch_model.update = True
            ch_model.new_content.extend(new_content)

    async def send_and_update(self, models_data: List[ChannelModel]) -> None:
        to_update = []
        to_send_tasks = []

        for ch_model in models_data:
            if ch_model.update:
                to_update.append(ch_model.channel)

            if ch_model.new_content:
                to_send_tasks.append(self.send_new_content(ch_model))

        if to_update:
            async with self.get_session() as async_session:
                await self.channel_manager.add_all(async_session, to_update)

        if to_send_tasks:
            await limit_gather(to_send_tasks, 15)

    def __build_content_msg(self, ch_model: ChannelModel) -> str:
        content_msgs = []

        for content_part in ch_model.new_content:
            content_url = self.YOUTUBE_BASE_URL + content_part

            content_mes = (
                f"<b><i>{settings.SMILES['orange_play']} Смотреть: "
                f"{content_url}</i></b>"
            )
            content_msgs.append(content_mes)

        content = "\n\n".join(content_msgs)
        return (
            f"{settings.SMILES['blue_ok']} <b><i>~ {ch_model.channel.name} ~"
            "\n\nНовый контент!"
            f"\n\n{content}</i></b>"
        )

    async def send_new_content(self, ch_model: ChannelModel) -> None:
        await self.message_controller.send_to_users(
            ch_model.users_tg_ids,
            self.__build_content_msg(ch_model),
            use_cache=True,
        )

    async def _check_db(self, url: str) -> Channel | None:
        async with self.get_session() as async_session:
            return await self.channel_manager.get_by_url(async_session, url)

    async def _check_web(self, url: str) -> str | None:
        response = await self.http_manager.get(url)

        if response:
            return response.text

        self.logger.warning('Can\'t load page: URL="%s"', url)

    async def __get_by_content_url(self, url: str) -> str | Channel | None:
        """
        Поиск URL канала по URL видео.
        """
        video_page = await self._check_web(url)
        if video_page is None:
            return

        channel_url = self.finder.find_channel_url(video_page, url)

        channel = await self._check_db(channel_url)
        if channel:
            return channel

        if channel_url is None:
            self.logger.warning(
                'Channel URL not found: Text="%s"',
                video_page if len(video_page) < 200 else video_page[:200],
            )
            return

        return await self._check_web(channel_url)

    async def get_channel(self, raw_url: str) -> Channel | None:
        """
        Возвращает канал из базы данных или создаёт
        его на основе страницы, по указанной ссылке.
        """
        channel = await self._check_db(raw_url)
        if channel:
            return channel

        if search(
            r"(?:/watch|videos|streams|shorts|playlists|community|channels|about|\?).+",
            raw_url,
        ):
            raw_channel = await self.__get_by_content_url(raw_url)

            if isinstance(raw_channel, Channel):
                return raw_channel

        else:
            raw_channel = await self._check_web(raw_url)

        if not raw_channel:
            return

        return await self.__build_new_channel(raw_channel, raw_url)

    async def __build_new_channel(self, raw_channel: str, url: str) -> Channel | None:
        name = self.finder.find_channel_name(raw_channel, url)
        original_url = self.finder.find_original_url(raw_channel, url)
        canonical_url = self.finder.find_canonical_url(raw_channel, url)

        if not name or not original_url or not canonical_url:
            return

        channel = Channel(
            name=name,
            url=original_url,
            canonical_url=canonical_url,
            last_videos=[],
            last_streams=[],
        )
        channel_model = ChannelModel(channel=channel)

        await self.get_content([channel_model])
        self.analise_found_content([channel_model])

        return channel_model.channel

    async def proces_raw_channel(
        self,
        raw_url: str,
        user: User,
    ) -> Channel | None:
        channel = await self.get_channel(raw_url)
        if not channel:
            return

        async with self.get_session() as async_session:
            if not channel.id:
                await self.channel_manager.add_with_association(
                    async_session,
                    user,
                    channel,
                )

                self.logger.info(
                    'Added channel: Channel="%s"',
                    channel.name,
                )

            else:
                association = await self.association_manager.exists(
                    async_session,
                    user,
                    channel,
                )

                if not association:
                    association = Association(user_id=user.id, channel_id=channel.id)
                    await self.association_manager.add(async_session, association)

        return channel

    async def show_channels(
        self,
        channels: Sequence[Channel],
        message: Message,
        state: FSMContext,
    ) -> None:
        async with state.proxy() as data:
            channel_msg_dict: Dict[int, Tuple[Message, Channel]] = {}

            for channel in channels:
                text = (
                    f"<i><b>{settings.SMILES['green_ok']} ~ {channel.name} ~\n\n"
                    f"YouTube: {settings.SMILES['r_arrow']} {channel.url}</b></i>"
                )

                ch_mes = await self.message_controller.send_message(
                    message.chat.id,
                    text,
                    reply_markup=unsub_keyboard,
                    disable_web_page_preview=True,
                )

                channel_msg_dict[ch_mes.message_id] = (ch_mes, channel)

            data["channels"] = channel_msg_dict
