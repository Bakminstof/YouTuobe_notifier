from asyncio import gather
from typing import AsyncContextManager, Callable, Sequence

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload

from controllers.messages import MessageController
from filters import AdminFilter
from models.managers import UserManager, get_session
from models.schemas import User
from settings import settings


class AdminHandler:
    def __init__(self) -> None:
        self.get_session: Callable[
            [None],
            AsyncContextManager[AsyncSession],
        ] = get_session  # type: ignore

        self.message_controller: MessageController = MessageController()

        self.user_manager: UserManager = UserManager()

    @classmethod
    def __build_user_info(cls, user: User) -> str:
        """
        Used field:
        first_name, blocked, auth_timestamp
        """
        user_str = f"<b>{settings.SMILES['medium_bs']} {user.first_name} "
        blocked_str = f"{settings.SMILES['block'] if user.blocked else ''}</b>\n"
        auth_str = f"<i>{user.auth_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>"
        return user_str + blocked_str + auth_str

    async def show_users(self, message: Message, state: FSMContext) -> None:
        chat_id = message.chat.id

        async with self.get_session() as async_session:
            users: Sequence[User] = await self.user_manager.get(
                async_session,
                options=[
                    load_only(User.first_name, User.blocked, User.auth_timestamp),
                    noload(User.channels),
                ],
                order_by=User.auth_timestamp.desc(),
            )

        if users:
            users_str = []

            for user in users:
                users_str.append(self.__build_user_info(user))

            mes = "\n\n".join(users_str)

            await self.message_controller.send_message(chat_id, mes)

        else:
            await self.message_controller.send_message(chat_id, "Пользователей нет")

    async def check_users(self, message: Message, state: FSMContext) -> None:
        async with self.get_session() as async_session:
            users: Sequence[User] = await self.user_manager.get(
                async_session,
                options=[load_only(User.telegram_id), noload(User.channels)],
            )

        chat_ids = [user.telegram_id for user in users]

        messages = await self.message_controller.send_to_users(
            chat_ids,
            settings.SMILES["hand"],
        )

        tasks = [
            self.message_controller.delete_message(chat_id, message.message_id)
            for chat_id, message in zip(chat_ids, messages)
            if message
        ]

        await gather(*tasks)

        await self.message_controller.send_message(
            message.chat.id, settings.SMILES["green_ok"]
        )

    async def param(self, message: Message, state: FSMContext) -> None:
        chat_id = message.chat.id

        text = (
            f"{settings.SMILES['gear']}\n\n"
            "/param - <i>показать доп. параметры</i>\n\n"
            "/show_users - <i>список пользователей</i>\n\n"
            "/check_users - <i>проверить пользователей на блокировку</i>\n\n"
        )

        await self.message_controller.send_message(
            chat_id,
            text,
            disable_web_page_preview=True,
        )

    def register(self, dispatcher: Dispatcher) -> None:
        dispatcher.register_message_handler(
            self.show_users,
            AdminFilter(command="show_users"),
        )
        dispatcher.register_message_handler(
            self.check_users,
            AdminFilter(command="check_users"),
        )
        dispatcher.register_message_handler(
            self.param,
            AdminFilter(command="param"),
        )
