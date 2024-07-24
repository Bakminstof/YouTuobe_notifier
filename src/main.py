from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from core.lifespan import Lifespan
from core.settings import settings
from core.utils import start_webhook
from routers import admin_router, channels_router, info_router, start_router


def setup_dispatcher(dispatcher: Dispatcher, lifespan: Lifespan) -> None:
    dispatcher.startup.register(lifespan.on_startup)
    dispatcher.shutdown.register(lifespan.on_shutdown)
    dispatcher.include_routers(
        admin_router,
        start_router,
        info_router,
        channels_router,
    )


def setup() -> tuple[Dispatcher, Bot]:
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=settings.parse_mod),
    )
    lifespan = Lifespan(bot)

    setup_dispatcher(dispatcher, lifespan)

    return (
        dispatcher,
        bot,
    )


def start() -> None:
    dp, bot = setup()

    if settings.webhook.active:
        start_webhook(dp, bot)

    else:
        import asyncio

        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    start()
