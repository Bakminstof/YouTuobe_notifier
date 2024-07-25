from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from controllers.message_ctrl import send_message
from core.models import UtilMessages
from filters import AdminFilter
from routers.info.utils import send_info

router = Router(name="info")


@router.message(AdminFilter(), Command("info"))
async def admin_info(message: Message, bot: Bot) -> None:
    await send_info(message, bot)
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=UtilMessages.admin_commands,
    )


@router.message(Command("info"))
async def info(message: Message, bot: Bot) -> None:
    await send_info(message, bot)
