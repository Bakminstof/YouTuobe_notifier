from logging import getLogger

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramUnauthorizedError,
)
from aiogram.types import InlineKeyboardMarkup, Message, MessageEntity

from core.settings import settings
from database.tps import Status
from database.utils import get_profile_db
from utils.token_bucket import rate_limit

logger = getLogger(__name__)


@rate_limit("Telegram")
async def delete_message(msg: Message | None) -> bool | None:
    if msg is None:
        return

    try:
        deleted = await msg.delete()

    except TelegramBadRequest:
        deleted = False

    logger.info(
        'Message delete %s: message_id="%s", sender_tg_id="%s", chat_id="%s". Text: %s',
        "success" if deleted else "failure",
        msg.message_id,
        msg.from_user.id,
        msg.chat.id,
        msg.text,
    )

    return deleted


@rate_limit("Telegram")
async def edit_message(
    msg: Message | None,
    text: str,
    entities: list[MessageEntity] | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    disable_web_page_preview: bool = False,
) -> Message | bool | None:
    if msg is None:
        return

    try:
        edited = await msg.edit_text(
            text,
            entities=entities,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )
    except TelegramBadRequest:
        edited = False

    logger.info(
        'Message edit %s: message_id="%s", sender_tg_id="%s", chat_id="%s". Text: %s',
        "success" if edited else "failure",
        msg.message_id,
        msg.from_user.id,
        msg.chat.id,
        msg.text,
    )

    return edited


@rate_limit("Telegram")
async def send_message(
    bot: Bot,
    chat_id: int,
    user_tg_id: int,
    text: str,
    entities: list[MessageEntity] | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    disable_web_page_preview: bool = False,
    timeout: int = settings.requests_timeout,
) -> Message | None:
    msg = None

    try:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            entities=entities,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            request_timeout=timeout,
        )

    except (TelegramUnauthorizedError, TelegramForbiddenError, TelegramBadRequest):
        async with get_profile_db() as profile_db:
            user_profile = await profile_db.get_by_tg_id(user_tg_id)

        logger.warning(
            'Bot blocked by user: username="%s", user_tg_id="%s"',
            user_profile.username,
            user_tg_id,
        )

        async with get_profile_db() as profile_db:
            to_update = {"id": user_profile.id, "status": Status.blocked}
            await profile_db.update([to_update])

    except TelegramNetworkError as ex:
        logger.warning(
            'Network error: message="%s", url=%s, method="%s", label="%s"',
            ex.message,
            ex.url,
            ex.method,
            ex.label,
        )

    logger.info(
        'Send message %s: message_id="%s", user_tg_id="%s", chat_id="%s"%s',
        "success" if msg else "failure",
        msg.message_id if msg else None,
        user_tg_id,
        chat_id,
        f". Text: {msg.text}" if msg else "",
    )

    return msg
