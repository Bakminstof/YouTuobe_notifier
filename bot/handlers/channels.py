from contextlib import suppress
from logging import Logger, getLogger
from re import search
from typing import AsyncContextManager, Callable

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from controllers import ChannelController, MessageController
from keyboards.inline import callback_channel, sub_keyboard, unsub_keyboard
from models.managers import AssociationManager, ChannelManager, UserManager, get_session
from models.schemas import Association, Channel, User
from settings import settings


class ChannelHandler:
    logger: Logger = getLogger(__name__)

    def __init__(self) -> None:
        self.get_session: Callable[
            [None],
            AsyncContextManager[AsyncSession],
        ] = get_session  # type: ignore

        self.channel_controller: ChannelController = ChannelController()
        self.message_controller: MessageController = MessageController()

        self.association_manager: AssociationManager = AssociationManager()
        self.channel_manager: ChannelManager = ChannelManager()
        self.user_manager: UserManager = UserManager()

    async def get_channels(self, message: Message, state: FSMContext) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        await self.message_controller.clear_channels_data(user_id, state)
        await state.reset_state()

        async with self.get_session() as async_session:
            channels = await self.channel_manager.get_user_channels(
                async_session,
                user_id,
                order_by=Channel.id.desc(),
            )

        if channels:
            await self.channel_controller.show_channels(channels, message, state)

        else:
            await self.message_controller.send_message(
                chat_id,
                "Ваш список пуст. Вставьте ссылку на Youtube канал",
            )

    async def channel_add(self, message: Message, state: FSMContext) -> None:
        chat_id = message.chat.id

        raw_url = search("https://.*", message.text)

        if not raw_url:
            text = f"Не могу распознать ссылку {settings.SMILES['sad_face']}."
            await self.message_controller.send_message(chat_id, text)
            return

        user_id = message.from_user.id

        async with self.get_session() as async_session:
            user, channel_limit = await self.user_manager.get_with_channel_limit(
                async_session,
                user_id,
                options=[
                    load_only(User.id, User.add_subs_count),
                ],
            )

        text = f"Дайте-ка подумать... {settings.SMILES['stone_face']}"

        mes = await self.message_controller.send_message(chat_id, text)

        if channel_limit:
            await self.__limit(mes)
            return

        await self.message_controller.clear_channels_data(user_id, state)
        await state.reset_state()

        try:
            channel = await self.channel_controller.proces_raw_channel(
                raw_url.group(),
                user,
            )

            if channel:
                await self.channel_controller.show_channels(
                    [channel],
                    mes,
                    state,
                )

            else:
                text = (
                    f"Не могу найти канал {settings.SMILES['sad_face']}. "
                    f"Попробуйте другую ссылку"
                )

                await self.message_controller.send_message(chat_id, text)

        finally:
            await mes.delete()

    async def subscribe(self, call: CallbackQuery, state: FSMContext) -> None:
        data = await self.message_controller.load_channel_msg_data(call, state)

        if data:
            message, channel, user, channel_limit = data

            if channel_limit:
                await self.__limit(message)
            else:
                await self.__subscribe(message, channel, user)

    async def unsubscribe(self, call: CallbackQuery, state: FSMContext) -> None:
        data = await self.message_controller.load_channel_msg_data(call, state)

        if data:
            message, channel, user, _ = data
            await self.__unsubscribe(message, channel, user)

    async def __subscribe(
        self,
        message: Message,
        channel: Channel,
        user: User,
    ) -> None:
        text = f"<b><i>{settings.SMILES['green_ok']}{message.text[1:]}</i></b>"

        await self.message_controller.edit_message(
            message,
            text,
            unsub_keyboard,
        )

        async with self.get_session() as async_session:
            with suppress(IntegrityError):  # Spam button control
                association = Association(user_id=user.id, channel_id=channel.id)
                await self.association_manager.add(async_session, association)

        self.logger.debug(
            'Subscription: User="%s" -> Channel="%s"',
            user.first_name,
            channel.name,
        )

    async def __unsubscribe(
        self,
        message: Message,
        channel: Channel,
        user: User,
    ) -> None:
        text = f"<b><i>{settings.SMILES['no']}{message.text[1:]}</i></b>"

        await self.message_controller.edit_message(
            message,
            text,
            sub_keyboard,
        )

        async with self.get_session() as async_session:
            with suppress(IntegrityError):  # Spam button control
                await self.association_manager.delete(async_session, user, channel)

        self.logger.debug(
            'Unsubscribe: User="%s" X Channel="%s"',
            user.first_name,
            channel.name,
        )

    async def __limit(self, message: Message) -> None:
        text = (
            f"\n\n{settings.SMILES['stop']} "
            f"У вас лимит подписок {settings.SMILES['stop']}"
        )

        await self.message_controller.edit_message(
            message,
            text,
        )

    def register(self, dispatcher: Dispatcher) -> None:
        dispatcher.register_message_handler(
            self.get_channels,
            commands=["channels"],
        )
        dispatcher.register_message_handler(self.channel_add)
        dispatcher.register_callback_query_handler(
            self.subscribe,
            callback_channel.filter(action="sub"),
        )
        dispatcher.register_callback_query_handler(
            self.unsubscribe,
            callback_channel.filter(action="unsub"),
        )
