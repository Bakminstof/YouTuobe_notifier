from aiogram import Bot
from aiogram.types import Message

from controllers.message_ctrl import send_message
from core.settings import settings


async def send_info(message: Message, bot: Bot) -> None:
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
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=settings.bot_msg_utils.messages["info"],
    )
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=f"{settings.bot_msg_utils.smiles['lifebuoy']} "
        f"<b><i>Техподдержка бота:</i></b>\n{settings.support}",
    )
