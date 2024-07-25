from contextlib import suppress
from logging import getLogger

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import load_only

from apps.notifier.models import ContentType, UserFSMmodel
from apps.notifier.utils import save_streams_urls, save_videos_urls
from controllers.message_ctrl import delete_message, edit_message, send_message
from core.models import Smiles
from core.settings import settings
from database.schemas import Channel, Profile, ProfileChannelAssociation
from database.utils import get_channel_db, get_prof_ch_association_db, get_profile_db
from keyboards.inline.channel_keyboards import sub_keyboard, unsub_keyboard
from utils.finder import find_canonical_url, find_channel_name, find_original_url
from utils.scrapper import get_channel_page, get_content_urls

logger = getLogger(__name__)


async def save_new_channel(channel: Channel, profile: Profile) -> Channel:
    async with get_channel_db() as channel_db:
        association = ProfileChannelAssociation(
            profile_id=profile.id, channel_id=channel.id
        )
        channel.profile_associations.append(association)
        return await channel_db.create([channel])


async def save_new_channel_content(channel: Channel) -> None:
    videos = await get_content_urls(channel.url, ContentType.videos)
    streams = await get_content_urls(channel.url, ContentType.streams)

    await save_videos_urls(channel.id, videos)
    await save_streams_urls(channel.id, streams)


async def get_user_data(tg_id: int, state: FSMContext) -> UserFSMmodel:
    state_data = await state.get_data()
    user: UserFSMmodel | None = state_data.get(str(tg_id))

    if user is None:
        async with get_profile_db() as profile_db:
            profile = await profile_db.get_by_tg_id(
                tg_id, options=[load_only(Profile.subs_limit)]
            )

        async with get_channel_db() as channels_db:
            channels = await channels_db.get_user_channels(tg_id)

        user = UserFSMmodel(profile=profile, channels=channels)
        await state.set_data({str(tg_id): user})

    return user


async def update_user_channels(tg_id: int, state: FSMContext) -> list[Channel]:
    user_data: UserFSMmodel = await get_user_data(tg_id, state)

    async with get_channel_db() as channels_db:
        channels = await channels_db.get_user_channels(tg_id)
        user_data.channels = channels
        await state.set_data({str(tg_id): user_data})
        return channels


async def set_displayed_channels(
    tg_id: int,
    state: FSMContext,
    displayed_channels: dict[int, tuple[Message, Channel]],
) -> None:
    user_data: UserFSMmodel = await get_user_data(tg_id, state)
    user_data.displayed_channels = displayed_channels
    await state.set_data({str(tg_id): user_data})


async def clear_displayed_channels(tg_id: int, state: FSMContext) -> None:
    user_data: UserFSMmodel = await get_user_data(tg_id, state)

    for message, channel in user_data.displayed_channels.values():
        await delete_message(message)

    user_data.displayed_channels.clear()
    await state.set_data({str(tg_id): user_data})


async def show_channels(
    bot: Bot,
    chat_id: int,
    tg_id: int,
    state: FSMContext,
    *,
    channels: list[Channel] | None = None,
) -> None:
    user_data = await get_user_data(tg_id, state)

    if channels is None:
        channels = user_data.channels
        displayed_channels = {}

    else:
        displayed_channels = user_data.displayed_channels

    for channel in channels:
        ch_mes = await send_message(
            bot=bot,
            chat_id=chat_id,
            user_tg_id=tg_id,
            text=f"<i><b>{Smiles.green_ok} ~ {channel.name} ~\n\n"
            f"YouTube: {Smiles.r_arrow} {channel.url}</b></i>",
            reply_markup=unsub_keyboard,
            disable_web_page_preview=True,
        )

        displayed_channels[ch_mes.message_id] = (ch_mes, channel)

    await set_displayed_channels(tg_id, state, displayed_channels)


async def limit_channels(message_to_edit: Message) -> None:
    await edit_message(
        msg=message_to_edit,
        text=f"{Smiles.stop} " f"У вас лимит подписок {Smiles.stop}",
    )


async def channel_subscribe(
    message: Message,
    channel: Channel,
    profile: Profile,
    state: FSMContext,
) -> None:
    await edit_message(
        msg=message,
        text=f"<b><i>{Smiles.green_ok}{message.text[1:]}</i></b>",
        reply_markup=unsub_keyboard,
        disable_web_page_preview=True,
    )

    async with get_prof_ch_association_db() as prof_ch_association_db:
        with suppress(IntegrityError):  # Spam button control
            association = ProfileChannelAssociation(
                profile_id=profile.id, channel_id=channel.id
            )
            await prof_ch_association_db.create([association])

    await update_user_channels(profile.tg_id, state)

    logger.debug(
        'Subscription: User="%s" -> Channel="%s"',
        profile.first_name,
        channel.name,
    )


async def channel_unsubscribe(
    message: Message,
    channel: Channel,
    profile: Profile,
    state: FSMContext,
) -> None:
    await edit_message(
        msg=message,
        text=f"<b><i>{Smiles.no}{message.text[1:]}</i></b>",
        reply_markup=sub_keyboard,
        disable_web_page_preview=True,
    )

    async with get_prof_ch_association_db() as prof_ch_association_db:
        with suppress(IntegrityError):  # Spam button control
            await prof_ch_association_db.delete(
                profile_id=profile.id, channel_id=channel.id
            )

    await update_user_channels(profile.tg_id, state)

    logger.info(
        'Unsubscribe: User="%s" X Channel="%s"',
        profile.first_name,
        channel.name,
    )


async def get_channel(raw_url: str) -> Channel | None:
    """Возвращает канал, созданный по ссылке YouTube"""
    channel_page = await get_channel_page(raw_url)

    if channel_page:
        return await __build_new_channel(channel_page, raw_url)


async def __build_new_channel(channel_page: str, url: str) -> Channel | None:
    name = find_channel_name(channel_page, url)
    original_url = find_original_url(channel_page, url)
    canonical_url = find_canonical_url(channel_page, url)

    if not name or not original_url or not canonical_url:
        return

    return Channel(
        name=name,
        url=original_url,
        canonical_url=canonical_url,
    )


async def bad_url(bot: Bot, message: Message) -> None:
    await send_message(
        bot=bot,
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        text=f"Не могу распознать ссылку {Smiles.sad_face}",
    )
    return
