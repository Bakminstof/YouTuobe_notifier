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
from core.models import Status
from database.utils import get_profile_db
from utils.token_bucket import rate_limit

logger = getLogger(__name__)


@rate_limit("Telegram")
async def delete_message(message: Message | None) -> bool:
    if message is None:
        return False

    logger.info(
        "Try delete message. "
        '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
        message.message_id,
        message.from_user.id,
        message.chat.id,
        message.text,
    )

    try:
        deleted_result = await message.delete()

        logger.info(
            "Message delete success. "
            '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
            message.message_id,
            message.from_user.id,
            message.chat.id,
            message.text,
        )

    except TelegramBadRequest as ex:
        deleted_result = False

        logger.warning(
            "Message delete failure. Exception message: %s. "
            '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
            ex.message,
            message.message_id,
            message.from_user.id,
            message.chat.id,
            message.text,
        )

    return deleted_result


@rate_limit("Telegram")
async def edit_message(
    message: Message | None,
    text: str,
    entities: list[MessageEntity] | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    disable_web_page_preview: bool = False,
) -> Message | None:
    if message is None:
        return

    logger.info(
        "Try edit message. "
        '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
        message.message_id,
        message.from_user.id,
        message.chat.id,
        message.text,
    )

    try:
        edited_message = await message.edit_text(
            text,
            entities=entities,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )

        logger.info(
            "Message edit success. "
            '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
            message.message_id,
            message.from_user.id,
            message.chat.id,
            message.text,
        )

    except TelegramBadRequest as ex:
        edited_message = None

        logger.warning(
            "Message edit failure. Exception message: %s. "
            '(message_id="%s" | sender_tg_id="%s" | chat_id="%s" | text="%s")',
            ex.message,
            message.message_id,
            message.from_user.id,
            message.chat.id,
            message.text,
        )

    return edited_message


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
    logger.info(
        'Try send message. (user_tg_id="%s" | chat_id="%s" | text="%s")',
        user_tg_id,
        chat_id,
        text,
    )

    try:
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            entities=entities,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            request_timeout=timeout,
        )

        logger.info(
            "Send message success. "
            '(message_id="%s" | user_tg_id="%s" | chat_id="%s" | text="%s")',
            message.message_id,
            user_tg_id,
            chat_id,
            text,
        )

        return message

    except (TelegramUnauthorizedError, TelegramForbiddenError, TelegramBadRequest):
        async with get_profile_db() as profile_db:
            user_profile = await profile_db.get_by_tg_id(user_tg_id)

            to_update = {"id": user_profile.id, "status": Status.blocked}
            await profile_db.update([to_update])

        logger.warning(
            'Bot blocked by user. (username="%s" | user_tg_id="%s")',
            user_profile.username,
            user_tg_id,
        )

    except TelegramNetworkError as ex:
        logger.warning(
            "Telegram network error. Exception message: %s. "
            '(url=%s | method="%s" | label="%s")',
            ex.message,
            ex.url,
            ex.method,
            ex.label,
        )
