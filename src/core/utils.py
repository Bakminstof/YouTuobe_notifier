from logging import getLogger
from logging.config import dictConfig
from ssl import PROTOCOL_TLSv1_2, SSLContext
from warnings import warn

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application, run_app

from core.lifespan import Lifespan
from core.settings import settings
from routers import (
    start_router,
    admin_router,
    channels_router,
    info_router,
)

__all__ = ("start",)


logger = getLogger(__name__)


def __get_tls_context() -> SSLContext:
    context = SSLContext(PROTOCOL_TLSv1_2)
    context.load_cert_chain(
        settings.webhook.public_key.path.absolute(),
        settings.webhook.private_key.path.absolute(),
    )
    return context


def _setup() -> tuple[Dispatcher, Bot]:
    __setup_logging()

    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=settings.parse_mod),
    )
    lifespan = Lifespan(bot)

    __setup_dispatcher(dispatcher, lifespan)

    return dispatcher, bot


def __setup_logging() -> None:
    dictConfig(settings.logging.dict_config)

    if settings.debug:
        msg = "Debug mode on"
        logger.warning(msg)
        warn(msg, UserWarning)

    else:
        if settings.logging.sentry:
            import sentry_sdk  # type: ignore

            sentry_sdk.init(settings.logging.sentry, traces_sample_rate=1)


def __setup_request_handler(dispatcher: Dispatcher, bot: Bot, app: Application) -> None:
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.secret_token,
    )

    webhook_requests_handler.register(
        app,
        path=settings.webhook.path(bot_token=settings.bot_token),
    )


def __setup_dispatcher(dispatcher: Dispatcher, lifespan: Lifespan) -> None:
    dispatcher.startup.register(lifespan.on_startup)
    dispatcher.shutdown.register(lifespan.on_shutdown)

    dispatcher.include_routers(
        admin_router,
        start_router,
        info_router,
        channels_router,
    )


def start_webhook(dispatcher: Dispatcher, bot: Bot) -> None:
    app = Application()

    setup_application(app, dispatcher, bot=bot)
    __setup_request_handler(dispatcher, bot, app)

    ssl_context = __get_tls_context() if not settings.webhook.reverse_proxy else None

    run_app(
        app,
        host=settings.webhook.web_server_host,
        port=settings.webhook.web_server_port,
        ssl_context=ssl_context,
    )


def start_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    import asyncio

    asyncio.run(dispatcher.start_polling(bot))


def start() -> None:
    dp, bot = _setup()

    if settings.webhook.active:
        start_webhook(dp, bot)

    else:
        start_polling(dp, bot)
