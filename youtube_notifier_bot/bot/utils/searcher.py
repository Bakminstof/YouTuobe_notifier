from asyncio import sleep
from logging import getLogger
from time import time
from typing import List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from db.schemas import Association, Channel, Temp, User
from utils.channel_manager import ChannelManager
from utils.http_manager import HTTPManager
from utils.sender import CACHE, Sender

logger = getLogger(__name__)


class Searcher:
    SLEEP_TIME = 5 * 60

    @classmethod
    async def start(cls, async_session: async_sessionmaker[AsyncSession]) -> None:
        while True:
            try:
                await cls.search(async_session)

            except Exception as ex:
                logger.exception('Search cycle error: Type="%s" | %s', type(ex), ex)

                await sleep(5)

    @classmethod
    def __build_chms(cls, channels: Sequence[Channel]) -> List[ChannelManager]:
        channel_managers = []

        for channel in channels:
            channel_manager = ChannelManager(channel)
            channel_managers.append(channel_manager)

        return channel_managers

    @classmethod
    def __clear_chms(cls, channel_managers: List[ChannelManager]) -> None:
        for chm in channel_managers:
            chm.content_tasks.clear()
            chm.to_send.clear()

        channel_managers.clear()

    @classmethod
    async def __send_content_urls(cls, channel_managers: List[ChannelManager]) -> None:
        tasks = []

        for chm in channel_managers:
            tasks.append(chm.send())

        await Sender.limit_send(tasks)

    @classmethod
    async def __update(
        cls,
        channel_managers: List[ChannelManager],
        async_session: async_sessionmaker[AsyncSession],
    ) -> None:
        update_instances = []

        for chm in channel_managers:
            if chm.to_update:
                update_instances.append(chm.to_update.to_dict())

        await Channel.update(update_instances, async_session)

    @classmethod
    async def search(cls, async_session: async_sessionmaker[AsyncSession]) -> None:
        """
        Запускает цикл поиска.
        """
        while True:
            await Sender.check_temp_table(async_session)
            await sleep(5)

            start = time()

            logger.info("Start checking")

            channels = await Channel.get_channels_with_users(
                async_session,
                [
                    joinedload(Channel.users)
                    .joinedload(Association.user)
                    .load_only(User.id, User.telegram_id, User.blocked)
                ],
            )

            chms = cls.__build_chms(channels)

            tasks = [task for chm in chms for task in chm.content_tasks]

            await HTTPManager.limit_url_gather(tasks)

            await cls.__send_content_urls(chms)
            await cls.__update(chms, async_session)

            cls.__clear_chms(chms)

            if CACHE:
                await Temp.add_all(CACHE, async_session)

                CACHE.clear()

            sleep_time = cls.SLEEP_TIME

            logger.info(
                "Checking done at %d sec. Sleep %d sec.",
                round(time() - start, 2),
                sleep_time,
            )

            await sleep(sleep_time)
