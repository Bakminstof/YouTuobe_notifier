from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import lazyload, load_only

from db.core import async_session
from db.schemas import Association, Channel, User
from utils.channel_manager import ChannelManager
from utils.message_manager import MessageManager
from utils.sender import Sender


async def get_channels(message: Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await MessageManager.clear_channels_data(user_id, state)
    await state.reset_state()

    channels = await Channel.get_user_channels(
        User.telegram_id == user_id,
        async_session,
        options_set=[
            {load_only: (Channel.id, Channel.name, Channel.url)},
            lazyload(Channel.users).lazyload(Association.user),
        ],
        ordering=Channel.id.desc(),
    )

    if channels:
        await ChannelManager.view_channels(channels, message, state)

    else:
        await Sender.send_message(
            chat_id, "Ваш список пуст. Вставьте ссылку на Youtube канал"
        )


def register_channels(dp: Dispatcher) -> None:
    dp.register_message_handler(get_channels, commands=["channels"])
