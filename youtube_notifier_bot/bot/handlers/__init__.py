from aiogram import Dispatcher

from .admin import register_admin
from .base_handers import register_channels, register_info, register_start
from .channels import register_add_channel, register_sub_channel

registers = [
    register_admin,
    register_start,
    register_info,
    register_channels,
    register_add_channel,
    register_sub_channel,
]


def register_all(dispatcher: Dispatcher) -> None:
    for register in registers:
        register(dispatcher)


__all__ = ["register_all"]
