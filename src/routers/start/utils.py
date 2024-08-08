from logging import getLogger

from aiogram.types import User

from database.schemas import Profile
from core.models import Status
from database.utils import get_profile_db

logger = getLogger(__name__)


async def check_user(tg_user: User) -> None:
    async with get_profile_db() as profile_db:
        user_profile = await profile_db.get_by_tg_id(tg_user.id)

    if not user_profile:
        new_user_profile = Profile(
            tg_id=tg_user.id,
            username=tg_user.username if tg_user.usernamee else tg_user.first_name,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

        async with get_profile_db() as profile_db:
            await profile_db.create([new_user_profile])

        logger.info(
            'Add new user: User="%s"',
            new_user_profile.first_name,
        )

    else:
        user_profile.status = Status.active

        logger.info(
            'User is active: User="%s"',
            user_profile.first_name,
        )

        async with get_profile_db() as profile_db:
            to_update = {"id": user_profile.id, "status": Status.active}
            await profile_db.update([to_update])
