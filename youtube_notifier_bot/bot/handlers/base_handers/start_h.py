from datetime import datetime
from logging import getLogger

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import load_only

from config.msg_data import MESSAGES, SMILES
from db.core import async_session
from db.schemas import User
from utils.sender import Sender

logger = getLogger(__name__)


async def start(message: Message, state: FSMContext):
    user = await User.get(
        User.telegram_id == message.from_user.id,
        async_session,
        options_set=[{load_only: (User.id, User.blocked)}],
    )
    chat_id = message.chat.id

    if not user:
        new_user = User(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            auth_timestamp=datetime.now(),
        )

        await User.add(new_user, async_session)

        logger.info('Add new user: User="%s"', new_user.first_name)

    else:
        user.blocked = False

        await User.add(user, async_session)

    start_message = "Доброго времени суток, {name}! {hi}".format(
        name=message.from_user.first_name, hi=SMILES["hi"]
    )

    await Sender.send_message(chat_id, start_message)
    await Sender.send_message(chat_id, MESSAGES["HOW_WORK"])
    await Sender.send_message(
        chat_id, MESSAGES["WHAT_SEND"], disable_web_page_preview=True
    )


def register_start(dp: Dispatcher) -> None:
    dp.register_message_handler(start, commands=["start"])
