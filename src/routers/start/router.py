from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from controllers.message_ctrl import send_message
from core.settings import settings
from routers.start.utils import check_user

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message, bot: Bot) -> None:
    await check_user(message.from_user)

    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=f"Доброго времени суток, {message.from_user.first_name}! "
        f"{settings.bot_msg_utils.smiles['hi']}",
    )
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=settings.bot_msg_utils.messages["how_work"],
    )
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=settings.bot_msg_utils.messages["what_send"],
    )
