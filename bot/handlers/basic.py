from datetime import datetime
from logging import Logger, getLogger
from typing import AsyncContextManager, Callable, List, Sequence

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload

from controllers.messages import MessageController
from models.managers import UserManager, get_session
from models.schemas import User
from settings import settings


class BasicHandler:
    logger: Logger = getLogger(__name__)

    def __init__(self) -> None:
        self.get_session: Callable[
            [None],
            AsyncContextManager[AsyncSession],
        ] = get_session  # type: ignore

        self.message_controller: MessageController = MessageController()

        self.user_manager: UserManager = UserManager()

    async def __send_messages(self, chat_id: int, messages: List[str]) -> None:
        for message in messages:
            await self.message_controller.send_message(
                chat_id,
                message,
                disable_web_page_preview=True,
            )

    async def start(self, message: Message, state: FSMContext) -> None:
        async with self.get_session() as async_session:
            users: Sequence[User] = await self.user_manager.get(
                async_session,
                where=[User.telegram_id == message.from_user.id],
                options=[load_only(User.id, User.blocked), noload(User.channels)],
            )

        chat_id = message.chat.id

        if not users:
            new_user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                auth_timestamp=datetime.now(),
            )

            async with self.get_session() as async_session:
                await self.user_manager.add(async_session, new_user)

            self.logger.info(
                'Add new user: User="%s"',
                new_user.first_name,
            )

        else:
            user = users[0]

            user.blocked = False

            async with self.get_session() as async_session:
                await self.user_manager.add(async_session, user)

        start_message = (
            f"Доброго времени суток, {message.from_user.first_name}! "
            f"{settings.SMILES['hi']}"
        )

        messages = [
            start_message,
            settings.MESSAGES["HOW_WORK"],
            settings.MESSAGES["WHAT_SEND"],
        ]

        await self.__send_messages(chat_id, messages)

    async def info(self, message: Message, state: FSMContext) -> None:
        chat_id = message.chat.id

        messages = [
            settings.MESSAGES["HOW_WORK"],
            settings.MESSAGES["WHAT_SEND"],
            settings.MESSAGES["INFO"],
        ]

        await self.__send_messages(chat_id, messages)

    def register(self, dispatcher: Dispatcher) -> None:
        dispatcher.register_message_handler(
            self.start,
            commands=["start"],
        )
        dispatcher.register_message_handler(
            self.info,
            commands=["info"],
        )
