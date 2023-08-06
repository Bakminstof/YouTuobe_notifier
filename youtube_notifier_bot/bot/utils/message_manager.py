from typing import Dict, Tuple

from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import (
    MessageCantBeDeleted,
    MessageCantBeEdited,
    MessageNotModified,
    MessageToDeleteNotFound,
    MessageToEditNotFound,
)
from sqlalchemy.orm import load_only

from db.core import async_session
from db.schemas import Channel, User
from keyboards.inline import sub_keyboard
from loader import bot


class MessageManager:
    SUB_TEXT = "<b><i>{marker}{msg}{check_subs}</i></b>"

    @classmethod
    async def delete_message(cls, chat_id: int, mes_id: int) -> None:
        try:
            await bot.delete_message(chat_id, mes_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound, MessageNotModified):
            pass

    @classmethod
    async def clear_channels_data(cls, chat_id: int, state: FSMContext) -> None:
        async with state.proxy() as data:
            channels_dict = data.get("channels")

        if channels_dict:
            for mes_id in channels_dict.keys():
                await MessageManager.delete_message(chat_id, mes_id)

    @classmethod
    def __format_sub_text(cls, marker: str, msg: str, check_subs: str = "") -> str:
        return cls.SUB_TEXT.format(marker=marker, msg=msg, check_subs=check_subs)

    @classmethod
    async def edit_message(cls, message: Message, marker: str, check_subs: str = ""):
        try:
            text = cls.__format_sub_text(marker, message.text[1:], check_subs)
            await message.edit_text(text, reply_markup=sub_keyboard)
        except (MessageCantBeEdited, MessageToEditNotFound, MessageNotModified):
            pass

    @classmethod
    async def load_channel_msg_data(
        cls, call, state
    ) -> Tuple[Message, Channel, User, int] | None:
        user_id = call.from_user.id

        async with state.proxy() as data:
            mes_id = call.message.message_id

            channels: Dict[int, Tuple[Message, Channel]] = data.get("channels")

            if channels:
                pack = channels.get(mes_id)

                if pack:
                    channel_msg, channel = pack

                    user, limit = await User.get_with_channels_limit(
                        User.telegram_id == user_id,
                        async_session,
                        options_set=[
                            {
                                load_only: (
                                    User.id,
                                    User.first_name,
                                    User.add_subs_count,
                                )
                            },
                        ],
                    )

                    return channel_msg, channel, user, limit

        await cls.delete_message(call.message.chat.id, mes_id)
