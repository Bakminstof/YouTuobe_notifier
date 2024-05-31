import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from core.lifespan import Lifespan
from routers import start_router, info_router, admin_router, channels_router
from core.settings import settings
from core.utils import start_webhook


def start() -> None:
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=settings.parse_mod),
    )
    lifespan = Lifespan(bot)

    dispatcher.startup.register(lifespan.on_startup)
    dispatcher.shutdown.register(lifespan.on_shutdown)
    dispatcher.include_routers(admin_router, start_router, info_router, channels_router)

    if settings.webhook.active:
        start_webhook(dispatcher, bot)

    else:
        asyncio.run(dispatcher.start_polling(bot))


if __name__ == "__main__":
    start()
