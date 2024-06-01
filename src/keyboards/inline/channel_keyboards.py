from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.inline.channel_callbacks import ChannelCallback

sub_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Подписаться",
                callback_data=ChannelCallback(action="sub").pack(),
            ),
        ],
    ],
)

unsub_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отписаться",
                callback_data=ChannelCallback(action="unsub").pack(),
            ),
        ],
    ],
)
