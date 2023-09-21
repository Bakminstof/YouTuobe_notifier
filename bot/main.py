from logging.config import dictConfig
from typing import List, Type

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from controllers import MessageController
from handlers import AdminHandler, BasicHandler, ChannelHandler
from settings import settings
from utils.lifespan import Lifespan

storage: MemoryStorage = MemoryStorage()
bot: Bot = Bot(token=settings.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dispatcher: Dispatcher = Dispatcher(bot, storage=storage)
lifespan: Lifespan = Lifespan()

HANDLERS = [
    AdminHandler(),
    BasicHandler(),
    ChannelHandler(),
]

CONTROLLERS: List[Type[MessageController]] = [MessageController]


def init_controllers(dp: Dispatcher) -> None:
    for controller in CONTROLLERS:
        controller.init(dp)


def register_handlers(dp: Dispatcher) -> None:
    for handler in HANDLERS:
        handler.register(dp)


def start(dp: Dispatcher) -> None:
    dictConfig(settings.LOGGING)
    register_handlers(dp)
    init_controllers(dp)

    if settings.WEBHOOK:
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=settings.WEBHOOK_PATH,
            on_startup=lifespan.on_startup,
            on_shutdown=lifespan.on_shutdown,
            skip_updates=settings.SKIP_UPDATES,
            host=settings.WEBAPP_HOST,
            port=settings.WEBAPP_PORT,
            ssl_context=settings.TLS_CONTEXT,
        )

    else:
        executor.start_polling(
            dispatcher=dp,
            on_startup=lifespan.on_startup,
            on_shutdown=lifespan.on_shutdown,
            skip_updates=settings.SKIP_UPDATES,
        )


if __name__ == "__main__":
    start(dispatcher)
