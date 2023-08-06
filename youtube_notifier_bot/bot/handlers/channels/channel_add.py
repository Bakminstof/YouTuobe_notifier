from logging import Logger
from re import search

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import load_only

from config.msg_data import SMILES
from db.core import async_session
from db.schemas import User
from utils.channel_manager import ChannelManager
from utils.message_manager import MessageManager
from utils.sender import Sender

logger = Logger(__name__)

limit_message = "<b><i>{stop} У вас лимит подписок</i></b> {stop}".format(
    stop=SMILES["stop"]
)


async def channel_add(message: Message, state: FSMContext):
    chat_id = message.chat.id
    raw_url = search(r"https://.*", message.text)

    if raw_url:
        user_id = message.from_user.id

        user, limit = await User.get_with_channels_limit(
            User.telegram_id == user_id,
            async_session,
            options_set=[{load_only: (User.id, User.add_subs_count)}],
        )

        text = "Дайте-ка подумать... {stone_face}".format(stone_face=SMILES["stone_face"])

        mes = await Sender.send_message(chat_id, text)

        try:
            if limit:
                await Sender.send_message(chat_id, limit_message)

            else:
                await MessageManager.clear_channels_data(user_id, state)
                await state.reset_state()

                channel = await ChannelManager.proces_raw_channel(
                    async_session, raw_url, user
                )

                if channel:
                    await ChannelManager.view_channels([channel], mes, state)

                    logger.info('Added channel: Channel="%s"', channel.name)
                else:
                    text = "Не могу найти канал {}. Попробуйте другую ссылку".format(
                        SMILES["sad_face"]
                    )
                    await Sender.send_message(chat_id, text)

        finally:
            await mes.delete()

    else:
        text = "Не могу распознать ссылку {}.".format(SMILES["sad_face"])
        await Sender.send_message(chat_id, text)


def register_add_channel(dp: Dispatcher):
    dp.register_message_handler(channel_add)
