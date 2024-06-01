from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from controllers.message_ctrl import send_message
from filters import AdminFilter
from routers.admin.utils import build_user_description, get_profiles

router = Router(name="admin")


@router.message(AdminFilter(), Command("users"))
async def show_users(message: Message, bot: Bot) -> None:
    users = []

    async for profiles in get_profiles():
        for profile in profiles:
            users.append(build_user_description(profile))

        await send_message(
            bot=bot,
            chat_id=message.chat.id,
            user_tg_id=message.from_user.id,
            text="\n\n".join(users),
        )

    if not users:
        await send_message(
            bot=bot,
            chat_id=message.chat.id,
            user_tg_id=message.from_user.id,
            text="Пользователей нет",
        )
