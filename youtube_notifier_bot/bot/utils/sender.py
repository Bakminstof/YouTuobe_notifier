from asyncio import Semaphore, gather
from logging import getLogger
from typing import Any, Coroutine, List, Sequence

from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, NetworkError
from aiohttp import ClientConnectorError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import load_only

from db.core import async_session as a_session
from db.schemas import Temp, User
from loader import bot
from utils.decorators import rate_limit

logger = getLogger(__name__)

CACHE = []


class Sender:
    SEM = Semaphore()

    @classmethod
    @rate_limit(10, 1.5)
    async def limit_send(
        cls, tasks: List[Coroutine[Any, Any, Message | None]]
    ) -> List[Message | None]:
        return await gather(*tasks)  # noqa

    @classmethod
    async def check_temp_table(
        cls, async_session: async_sessionmaker[AsyncSession]
    ) -> None:
        temp: Sequence[Temp] = await Temp.get_all(async_session)

        if temp:
            logger.debug("Using cache table")

            tasks = []

            await Temp.delete_all(async_session)

            for item in temp:
                task = cls.send_message(chat_id=item.telegram_id, text=item.text)
                tasks.append(task)

            await cls.limit_send(tasks)

    @classmethod
    async def send_message_to_users(
        cls, users_ids: List[int], text: str, disable_web_page_preview: bool = False
    ) -> List[Message | None]:
        tasks = []

        for user_id in users_ids:
            tasks.append(
                cls.send_message(
                    user_id, text, disable_web_page_preview=disable_web_page_preview
                )
            )

        return await cls.limit_send(tasks)

    @classmethod
    async def send_message(
        cls,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup
        | ReplyKeyboardMarkup
        | ReplyKeyboardRemove
        | ForceReply
        | None = None,
        disable_web_page_preview: bool = False,
    ) -> Message | None:
        try:
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )

            logger.debug('Send message -> User ID="%d"', chat_id)

            return message

        except (NetworkError, ClientConnectorError, TimeoutError):
            tmp = Temp(telegram_id=chat_id, text=text)

            await cls.SEM.acquire()
            CACHE.append(tmp)
            cls.SEM.release()

            logger.warning('Network error. Can\'t send message ->X User ID="%d"', chat_id)

            return None

        except (BotBlocked, ChatNotFound):
            user = await User.get(
                User.telegram_id == chat_id,
                a_session,
                options_set=[{load_only: (User.id, User.blocked)}],
            )
            user.blocked = True

            await User.add(user, a_session)

            logger.warning('Bot blocked by user: User ID="%d"', chat_id)

            return None
