from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.inline.channel_callbacks import callback_channel

sub_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Подписаться",
                callback_data=callback_channel.new(action="sub"),
            ),
        ],
    ],
)

unsub_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отписаться",
                callback_data=callback_channel.new(action="unsub"),
            ),
        ],
    ],
)
