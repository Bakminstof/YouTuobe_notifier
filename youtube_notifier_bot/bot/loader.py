from logging import getLogger
from logging.config import dictConfig
from ssl import PROTOCOL_TLSv1_2, SSLContext

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from sentry_sdk import init

from config.env_settings import ENVSettings
from settings import LOGGING

logger = getLogger(__name__)

# BOT setup
env_settings = ENVSettings()
bot = Bot(token=env_settings.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Logging setup
dictConfig(LOGGING)

if env_settings.DEBUG:
    logger.warning("Debug mode on")
else:
    if env_settings.SENTRY:
        init(env_settings.SENTRY, traces_sample_rate=0.8)

# Webhook setup
if env_settings.WEBHOOK:
    ssl_context = SSLContext(PROTOCOL_TLSv1_2)

    with open(env_settings.WEBHOOK_TSL_CERTIFICATE, "rb") as serf:
        CERT = serf.read()

    SSL_CERTIFICATE = CERT

    ssl_context.load_cert_chain(
        env_settings.WEBHOOK_TSL_CERTIFICATE, env_settings.WEBHOOK_TSL_PRIVATE_KEY
    )

else:
    ssl_context = None
    SSL_CERTIFICATE = None
