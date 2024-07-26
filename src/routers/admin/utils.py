from asyncio import gather
from typing import AsyncGenerator, Sequence

from aiogram import Bot
from sqlalchemy.orm import load_only

from controllers.message_ctrl import send_message
from core.models import Smiles, Status
from core.settings import settings
from database.schemas import Profile
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
        status = Smiles.green_ok
    elif user_profile.status is Status.blocked:
        status = Smiles.block
    elif user_profile.status is Status.banned:
        status = Smiles.ban
    else:
        status = Smiles.skull

    user = f"{Smiles.medium_bs} {status} {user_profile.first_name}"
    auth_timestamp = f"<i>{user_profile.auth_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>"
    return f"<b>{user} {auth_timestamp}</b>"


async def notify_admins(bot: Bot, text: str) -> None:
    tasks = []

    for admin in settings.admins:
        tasks.append(send_message(bot=bot, chat_id=admin, user_tg_id=admin, text=text))

    await gather(*tasks)
