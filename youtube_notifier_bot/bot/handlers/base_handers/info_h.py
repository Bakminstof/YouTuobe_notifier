from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from config.msg_data import MESSAGES
from utils.sender import Sender


async def info(message: Message, state: FSMContext):
    chat_id = message.chat.id

    await Sender.send_message(chat_id, MESSAGES["HOW_WORK"])
    await Sender.send_message(
        chat_id, MESSAGES["WHAT_SEND"], disable_web_page_preview=True
    )
    await Sender.send_message(chat_id, MESSAGES["INFO"])


def register_info(dp: Dispatcher) -> None:
    dp.register_message_handler(info, commands=["info"])
