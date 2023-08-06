from aiogram.dispatcher.filters import Filter
from aiogram.types import Message

from loader import env_settings


class AdminFilter(Filter):
    def __init__(self, command: str, prefix: str = "/"):
        self.command = command
        self.prefix = prefix

    async def check(self, message: Message) -> bool:
        return (
            message.from_user.id in env_settings.ADMINS
            and message.text == self.prefix + self.command
        )
