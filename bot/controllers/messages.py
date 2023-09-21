from asyncio import Semaphore, gather
from contextlib import suppress
from logging import Logger, getLogger
from typing import AsyncContextManager, Callable, Dict, List, Sequence, Tuple

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.exceptions import (
    BotBlocked,
    ChatNotFound,
    MessageCantBeDeleted,
    MessageCantBeEdited,
    MessageNotModified,
    MessageToDeleteNotFound,
    MessageToEditNotFound,
    NetworkError,
)
from aiohttp import ClientConnectorError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload

from models.managers import TempManager, UserManager, get_session
from models.schemas import Channel, Temp, User
from utils.common import limit_gather


class MessageController:
    semaphore: Semaphore = Semaphore()

    CACHE: List[Temp] = []
    __DISPATCHER: Dispatcher | None = None

    logger: Logger = getLogger(__name__)

    def __init__(self) -> None:
        self.get_session: Callable[
            [None],
            AsyncContextManager[AsyncSession],
        ] = get_session  # type: ignore

        self.user_manager: UserManager = UserManager()
        self.temp_manager: TempManager = TempManager()

    @classmethod
    def init(cls, dispatcher: Dispatcher) -> None:
        cls.__DISPATCHER = dispatcher

    async def write_cache_into_db(self) -> None:
        await self.semaphore.acquire()

        if self.CACHE:
            async with self.get_session() as async_session:
                await self.temp_manager.add_all(async_session, self.CACHE)

            self.CACHE.clear()

        self.semaphore.release()

    async def __add_to_cache(self, chat_id: int, text: str) -> None:
        await self.semaphore.acquire()
        self.CACHE.append(Temp(telegram_id=chat_id, text=text))
        self.semaphore.release()

    async def __set_user_blocked(self, user_id: int) -> None:
        async with self.get_session() as async_session:
            users: Sequence[User] = await self.user_manager.get(
                async_session,
                where=[User.telegram_id == user_id],
                options=[
                    load_only(User.id, User.blocked),
                    noload(User.channels),
                ],
            )
        user = users[0]

        user.blocked = True

        async with self.get_session() as async_session:
            await self.user_manager.add(async_session, user)

    async def delete_message(self, chat_id: int, mes_id: int) -> None:
        if not self.__DISPATCHER:
            raise RuntimeError("Dispatcher is not initialised")

        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await self.__DISPATCHER.bot.delete_message(chat_id, mes_id)

    async def clear_channels_data(self, chat_id: int, state: FSMContext) -> None:
        async with state.proxy() as data:
            channels_dict = data.get("channels")

        if channels_dict:
            tasks = []

            for mes_id in channels_dict.keys():
                tasks.append(self.delete_message(chat_id, mes_id))

            await gather(*tasks)

    @classmethod
    async def edit_message(
        cls,
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        with suppress(
            MessageCantBeEdited,
            MessageToEditNotFound,
            MessageNotModified,
        ):
            await message.edit_text(text, reply_markup=reply_markup)

    async def __load_state_data(
        self,
        user_id: int,
        data: Tuple[Message, Channel] | None,
    ) -> Tuple[Message, Channel, User, bool] | None:
        if data:
            message, channel = data

            async with self.get_session() as async_session:
                user, channel_limit = await self.user_manager.get_with_channel_limit(
                    async_session,
                    user_id,
                    options=[
                        load_only(User.id, User.first_name, User.add_subs_count),
                    ],
                )

            return message, channel, user, channel_limit

    async def load_channel_msg_data(
        self,
        call: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[Message, Channel, User, bool] | None:
        user_id = call.from_user.id
        mes_id = call.message.message_id

        async with state.proxy() as data:
            channels_data: Dict[int, Tuple[Message, Channel]] | None = data.get(
                "channels",
            )

            if channels_data:
                return await self.__load_state_data(user_id, channels_data.get(mes_id))

        await self.delete_message(call.message.chat.id, mes_id)

    async def check_temp_table(self) -> None:
        async with self.get_session() as async_session:
            temp: Sequence[Temp] = await self.temp_manager.get_all(async_session)

        if temp:
            self.logger.debug("Using temp table")

            tasks = []

            async with self.get_session() as async_session:
                await self.temp_manager.delete(async_session)

            for item in temp:
                task = self.send_message(item.telegram_id, item.text)
                tasks.append(task)

            await limit_gather(tasks, 10, 1.5)

    async def send_to_users(
        self,
        users_ids: List[int],
        text: str,
        disable_web_page_preview: bool = False,
        use_cache: bool = False,
    ) -> List[Message | None]:
        tasks = []

        for user_id in users_ids:
            tasks.append(
                self.send_message(
                    user_id,
                    text,
                    disable_web_page_preview=disable_web_page_preview,
                    use_cache=use_cache,
                ),
            )

        return await limit_gather(tasks, 10, 1.5)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        disable_web_page_preview: bool = False,
        use_cache: bool = False,
    ) -> Message | None:
        if not self.__DISPATCHER:
            raise RuntimeError("Dispatcher is not initialised")

        try:
            message = await self.__DISPATCHER.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )

            self.logger.debug('Send message -> User ID="%d"', chat_id)

            return message

        except (NetworkError, ClientConnectorError, TimeoutError):
            if use_cache:
                await self.__add_to_cache(chat_id, text)

            self.logger.warning(
                'Network error. Can\'t send message ->X User ID="%d"',
                chat_id,
            )

        except (BotBlocked, ChatNotFound):
            await self.__set_user_blocked(chat_id)
            self.logger.warning('Bot blocked by user: User ID="%d"', chat_id)
