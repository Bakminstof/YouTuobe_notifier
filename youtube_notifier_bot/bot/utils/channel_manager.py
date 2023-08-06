from asyncio import gather
from logging import getLogger
from re import Match, search, sub
from typing import Any, Callable, Coroutine, Dict, List, Sequence, Tuple

from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import InstrumentedAttribute, load_only

from config.msg_data import SMILES
from db.schemas import Association, Channel, User
from keyboards.inline import unsub_keyboard
from utils.http_manager import HTTPManager
from utils.sender import Sender
from youtube.scrapper import Scrapper

logger = getLogger(__name__)


class ChannelManager:
    def __init__(self, channel: Channel):
        self.__channel = channel

        self.users_ids = [
            association.user.telegram_id
            for association in channel.users
            if not association.user.blocked
        ]
        self.new_content = {}

        self.to_update: Channel | None = None
        self.to_send: List[str] = []

        self.content_tasks: List[Coroutine] = []
        self.__get_content_tasks()

    @property
    def channel(self) -> Channel:
        return self.__channel

    @property
    def videos_url(self) -> str:
        return self.__channel.url + "/videos"

    @property
    def streams_url(self) -> str:
        return self.__channel.url + "/streams"

    @property
    def name(self) -> str:
        return self.__channel.name

    async def send(self) -> None:
        if self.to_send:
            youtube_url = "https://www.youtube.com"
            message = (
                "{marker} <b><i>~ {channel} ~\n\nНовый контент!\n\n{content}</i></b>"
            )

            content_msgs = []

            for content_part in self.to_send:
                video_url = youtube_url + content_part

                content_mes = (
                    "<b><i>{orange_play} Смотреть: "
                    "{video_url}</i></b>".format(
                        orange_play=SMILES["orange_play"], video_url=video_url
                    )
                )
                content_msgs.append(content_mes)

            text = message.format(
                marker=SMILES["blue_ok"],
                channel=self.name,
                content="\n\n".join(content_msgs),
            )

            await Sender.send_message_to_users(self.users_ids, text)

    def __get_content_tasks(self) -> None:
        self.content_tasks = [self.get_videos(), self.get_streams()]

    async def get_videos(self) -> None:
        await self.__get_new_content("video")

    async def get_streams(self) -> None:
        await self.__get_new_content("stream")

    async def __get_new_content(self, content_type: str) -> None:
        if content_type == "video":
            last_content_type = "last_video"
            url = self.videos_url

        elif content_type == "stream":
            last_content_type = "last_stream"
            url = self.streams_url

        else:
            logger.warning("Unsupported content type `%s`", content_type)
            return None

        res = await HTTPManager.get(url)

        if res:
            html_page = res.text

            self.__separate_content(last_content_type, html_page)

    def __separate_content(self, last_content_type: str, html_page: str) -> None:
        all_content = Scrapper.find_content_urls(self.channel.url, html_page)
        last_content = self.__channel.__getattribute__(last_content_type)
        new_content = []

        for item in all_content:
            if last_content not in all_content:
                if last_content is not None:
                    self.__channel.__setattr__(last_content_type, all_content[0])
                    self.to_update = self.__channel
                    break

                else:
                    new_content.append(item)

            elif item != last_content:
                new_content.append(item)

            else:
                break

        if new_content:
            self.__channel.__setattr__(last_content_type, new_content[0])

            self.to_send = new_content
            self.to_update = self.__channel

    @classmethod
    async def check_channel(
        cls,
        url: str,
        async_session: async_sessionmaker[AsyncSession],
        load_users: bool = False,
        options_set: Sequence[Dict[Callable, Sequence[InstrumentedAttribute]]]
        | Sequence[Any] = None,
    ) -> Channel | str | None:
        """
        Поиск канала по URL.
        """
        result = await Channel.get(
            Channel.url == url, async_session, load_users, options_set
        )

        if result:
            return result

        ch = await HTTPManager.get(url)

        if ch:
            return ch.text

        else:
            return None

    @classmethod
    async def view_channels(
        cls, channels: Sequence[Channel], message: Message, state: FSMContext
    ) -> None:
        async with state.proxy() as data:
            channel_msg_dict: Dict[int, Tuple[Message, Channel]] = {}

            for channel in channels:
                text = (
                    "<i><b>{check} ~ {name} ~\n\n"
                    "YouTube: {r_arrow} {url}</b></i>".format(
                        check=SMILES["green_ok"],
                        name=channel.name,
                        url=channel.url,
                        r_arrow=SMILES["r_arrow"],
                    )
                )

                ch_mes = await Sender.send_message(
                    message.chat.id,
                    text,
                    reply_markup=unsub_keyboard,
                    disable_web_page_preview=True,
                )

                channel_msg_dict[ch_mes.message_id] = (ch_mes, channel)

            data["channels"] = channel_msg_dict

    @classmethod
    async def get_channel_from(
        cls, data: str, async_session: async_sessionmaker[AsyncSession]
    ) -> Channel | str | None:
        url = Scrapper.find_channel_url(data)

        if url:
            return await cls.check_channel(
                url,
                async_session,
                options_set=[{load_only: (Channel.id, Channel.name, Channel.url)}],
            )

        else:
            return None

    @classmethod
    async def proces_raw_channel(
        cls, async_session: async_sessionmaker[AsyncSession], raw_url: Match, user: User
    ) -> Channel | None:
        url = sub(pattern="//[a-z.]+/", repl="//www.youtube.com/", string=raw_url.group())

        raw_channel = await cls.check_channel(
            url,
            async_session,
            options_set=[{load_only: (Channel.id, Channel.name, Channel.url)}],
        )

        if search(r"watch\?", url):
            raw_channel = await cls.get_channel_from(raw_channel, async_session)
            if raw_channel is None:
                return None

        if isinstance(raw_channel, Channel):
            association = await Association.check(user, raw_channel, async_session)

            if not association:
                await Association.add_association(user, raw_channel, async_session)

            return raw_channel

        elif isinstance(raw_channel, str):
            name = Scrapper.find_channel_name(raw_channel)

            if not name:
                return None

            chm = cls(Channel(url=url, name=name))

            tasks = [chm.get_videos(), chm.get_streams()]
            await gather(*tasks)

            await Channel.add_with_association(chm.channel, user, async_session)

            return chm.channel

        else:
            return None
