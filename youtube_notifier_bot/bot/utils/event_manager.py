from asyncio import all_tasks, get_running_loop
from logging import getLogger

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from db.connect import db_connect
from db.core import async_engine, async_session
from loader import SSL_CERTIFICATE, env_settings
from utils.searcher import Searcher
from utils.sender import Sender

logger = getLogger(__name__)


class EventHandler:
    @classmethod
    async def notify_admins(cls, message: str) -> None:
        users_ids = [admin_id for admin_id in env_settings.ADMINS]
        await Sender.send_message_to_users(users_ids, "<b>{}</b>".format(message))

    @classmethod
    async def set_default_commands(cls, bot: Bot):
        await bot.set_my_commands(
            [
                BotCommand("start", "Запустить бота"),
                BotCommand("channels", "Список подписок"),
                BotCommand("info", "Информация"),
            ]
        )

    @classmethod
    async def on_startup(cls, dispatcher: Dispatcher):
        logger.info("Startup bot")

        await db_connect()

        if env_settings.WEBHOOK:
            await dispatcher.bot.delete_webhook()

            await dispatcher.bot.set_webhook(
                url=env_settings.WEBHOOK_URL, certificate=SSL_CERTIFICATE
            )

        await cls.set_default_commands(dispatcher.bot)

        message = "Бот Запущен"

        await cls.notify_admins(message)

        loop = get_running_loop()

        loop.create_task(Searcher.start(async_session), name="cycle_search")

    @classmethod
    async def on_shutdown(cls, dispatcher: Dispatcher):
        logger.info("Shutdown bot")

        message = "Бот завершил работу"
        await cls.notify_admins(message)

        await cls.graceful_stop()

    @classmethod
    async def graceful_stop(cls):
        logger.info("Graceful stopping ...")

        task_cycles = [
            "cycle_search",
        ]

        loop = get_running_loop()

        for task in all_tasks(loop):
            if task.get_name() in task_cycles:
                task.cancel()

        await async_engine.dispose()
