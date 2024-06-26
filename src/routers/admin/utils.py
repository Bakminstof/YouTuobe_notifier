from asyncio import gather
from typing import AsyncGenerator, Sequence

from aiogram import Bot
from sqlalchemy.orm import load_only

from controllers.message_ctrl import send_message
from core.settings import settings
from database.models import Profile
from database.tps import Status
from database.utils import get_profile_db


async def get_profiles() -> AsyncGenerator[Sequence[Profile], None]:
    load_options = {
        "options": [
            load_only(
                Profile.id,
                Profile.first_name,
                Profile.status,
                Profile.auth_timestamp,
            )
        ]
    }

    async with get_profile_db() as profile_db:
        async for profiles in profile_db.aiter_load(
            profile_db.get, max_pages=10, per_page=100, **load_options
        ):  # type: Sequence[Profile]
            yield profiles


def build_user_description(
    user_profile: Profile,
) -> str:
    if user_profile.status is Status.active:
        status = settings.bot_msg_utils.smiles["green_ok"]
    elif user_profile.status is Status.blocked:
        status = settings.bot_msg_utils.smiles["block"]
    elif user_profile.status is Status.banned:
        status = settings.bot_msg_utils.smiles["ban"]
    else:
        status = settings.bot_msg_utils.smiles["skull"]

    user = f"{settings.bot_msg_utils.smiles['medium_bs']} {status} { user_profile.first_name}"
    auth_timestamp = f"<i>{user_profile.auth_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>"
    return f"<b>{user} {auth_timestamp}</b>"


async def notify_admins(bot: Bot, text: str) -> None:
    tasks = []

    for admin in settings.admins:
        tasks.append(send_message(bot=bot, chat_id=admin, user_tg_id=admin, text=text))

    await gather(*tasks)
