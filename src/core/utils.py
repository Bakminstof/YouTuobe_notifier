from logging import getLogger

from logging.config import dictConfig
from ssl import SSLContext, PROTOCOL_TLSv1_2
from warnings import warn

from aiogram import Dispatcher, Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from core.settings import settings

logger = getLogger(__name__)


def setup_logging() -> None:
    dictConfig(settings.logging.dict_config)

    if settings.debug:
        msg = "Debug mode on"
        logger.warning(msg)
        warn(msg, UserWarning)

    else:
        if settings.logging.sentry:
            import sentry_sdk  # type: ignore

            sentry_sdk.init(settings.logging.sentry, traces_sample_rate=1)


# ======================================|Webhook|======================================= #
def get_tls_context() -> SSLContext:
    context = SSLContext(PROTOCOL_TLSv1_2)
    context.load_cert_chain(
        settings.webhook.public_key.path.absolute(),
        settings.webhook.private_key.path.absolute(),
    )
    return context


def start_webhook(dispatcher: Dispatcher, bot: Bot) -> None:
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.secret_token,
    )

    webhook_requests_handler.register(
        app, path=settings.webhook.path(bot_token=settings.bot_token)
    )

    setup_application(app, dispatcher, bot=bot)

    web.run_app(
        app,
        host=settings.webhook.web_server_host,
        port=settings.webhook.web_server_port,
        ssl_context=get_tls_context() if not settings.webhook.reverse_proxy else None,
    )
