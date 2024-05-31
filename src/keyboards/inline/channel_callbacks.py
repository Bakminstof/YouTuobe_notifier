from aiogram.filters.callback_data import CallbackData


class ChannelCallback(CallbackData, prefix="channel"):
    action: str
