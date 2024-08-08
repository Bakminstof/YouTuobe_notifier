import asyncio
from logging import getLogger
from re import search

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from controllers.message_ctrl import delete_message, edit_message, send_message
from core.models import Smiles
from database.utils import get_channel_db
from keyboards.inline.channel_callbacks import ChannelCallback
from routers.channels.utils import (
    bad_url,
    channel_subscribe,
    channel_unsubscribe,
    clear_displayed_channels,
    get_channel,
    get_user_data,
    limit_channels,
    save_new_channel,
    save_new_channel_content,
    show_channels,
    update_user_channels,
)

logger = getLogger(__name__)
router = Router(name="channels")


@router.message(Command("channels"))
async def get_channels(message: Message, bot: Bot, state: FSMContext) -> None:
    await clear_displayed_channels(message.from_user.id, state)
    user_data = await get_user_data(message.from_user.id, state)
    channels = user_data.channels

    if channels:
        await show_channels(bot, message.chat.id, message.from_user.id, state)

    else:
        await send_message(
            bot=bot,
            chat_id=message.chat.id,
            user_tg_id=message.from_user.id,
            text="Ваш список пуст. Вставьте ссылку на Youtube канал",
        )


@router.message()
async def add_channel(message: Message, bot: Bot, state: FSMContext) -> None:
    if not message.text:
        return await bad_url(bot, message)

    raw_url = search("https://.*", message.text)

    if not raw_url:
        return await bad_url(bot, message)

    raw_url = raw_url.group()

    user_data = await get_user_data(message.from_user.id, state)
    profile = user_data.profile

    wait_mes = await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=f"Дайте-ка подумать... {Smiles.stone_face}",
    )

    if len(user_data.channels) >= profile.subs_limit:
        return await limit_channels(wait_mes)

    async with get_channel_db() as channel_db:
        channel = await channel_db.get_by_url(raw_url)

    if channel is None:
        channel = await get_channel(raw_url)

        if channel is None:
            await edit_message(
                message=wait_mes,
                text=f"Не могу найти канал {Smiles.sad_face}. "
                f"Попробуйте другую ссылку",
            )
            return

        async with get_channel_db() as channel_db:
            channel_from_db = await channel_db.get_by_url(channel.url)

        if channel_from_db is None:
            await save_new_channel(channel, profile)

            loop = asyncio.get_running_loop()
            loop.create_task(save_new_channel_content(channel))

    await update_user_channels(message.from_user.id, state)
    await delete_message(wait_mes)
    await show_channels(
        bot,
        message.chat.id,
        message.from_user.id,
        state,
        channels=[channel],
    )


@router.callback_query(ChannelCallback.filter(F.action == "sub"))
async def subscribe(call: CallbackQuery, state: FSMContext) -> None:
    user_data = await get_user_data(call.from_user.id, state)
    channel_data = user_data.displayed_channels.get(call.message.message_id)

    if not channel_data:
        await delete_message(call.message)
        return

    message, channel = channel_data
    profile = user_data.profile

    if len(user_data.channels) >= profile.subs_limit:
        await limit_channels(message)

    else:
        await channel_subscribe(message, channel, user_data.profile, state)


@router.callback_query(ChannelCallback.filter(F.action == "unsub"))
async def unsubscribe(call: CallbackQuery, state: FSMContext) -> None:
    user_data = await get_user_data(call.from_user.id, state)
    channel_data = user_data.displayed_channels.get(call.message.message_id)

    if not channel_data:
        await delete_message(call.message)
        return

    await channel_unsubscribe(channel_data[0], channel_data[1], user_data.profile, state)
