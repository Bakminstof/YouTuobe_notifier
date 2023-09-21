from asyncio import all_tasks, get_running_loop
from logging import Logger, getLogger

import sentry_sdk
from aiogram import Dispatcher
from aiogram.types import BotCommand

from controllers.messages import MessageController
from models.managers import db_session_manager
from settings import settings
from utils.notifier import Notifier


class Lifespan:
    logger: Logger = getLogger(__name__)
    message_controller: MessageController = MessageController()
    notifier: Notifier = Notifier()

    def __setup_logging(self) -> None:
        if settings.DEBUG:
            self.logger.warning("Debug mode on")
        else:
            if settings.SENTRY:
                sentry_sdk.init(settings.SENTRY, traces_sample_rate=0.8)

    @classmethod
    async def setup_webhook(cls, dispatcher: Dispatcher) -> None:
        await dispatcher.bot.delete_webhook()
        await dispatcher.bot.set_webhook(
            url=settings.WEBHOOK_URL,
            certificate=settings.TLS_CERTIFICATE,
        )

    @classmethod
    async def set_bot_command(cls, dispatcher: Dispatcher) -> None:
        await dispatcher.bot.set_my_commands(
            [
                BotCommand("start", "Запустить бота"),
                BotCommand("channels", "Список подписок"),
                BotCommand("info", "Информация"),
            ],
        )

    @classmethod
    async def init_session_manager(cls) -> None:
        db_session_manager.init(
            engine_url=settings.DB_URL,
            echo_sql=settings.ECHO_SQL,
            init_db=settings.FORCE_INIT,
        )

        await db_session_manager.inspect()

    def __start_notifier(self) -> None:
        loop = get_running_loop()
        loop.create_task(self.notifier.start(), name=self.notifier.cycle_name)

    async def on_startup(self, dispatcher: Dispatcher) -> None:
        self.__setup_logging()

        self.logger.info("Startup bot")

        await self.init_session_manager()
        await self.set_bot_command(dispatcher)

        if settings.WEBHOOK:
            await self.setup_webhook(dispatcher)

        self.__start_notifier()

        await self.message_controller.send_to_users(settings.ADMINS, "Бот Запущен")

    async def on_shutdown(self, dispatcher: Dispatcher) -> None:
        self.logger.info("Shutdown bot")

        self.notifier.stop()

        await self.message_controller.send_to_users(
            settings.ADMINS,
            "Бот завершил работу",
        )

        task_cycles = [
            self.notifier.cycle_name,
        ]

        loop = get_running_loop()

        for task in all_tasks(loop):
            if task.get_name() in task_cycles:
                task.cancel()

        await db_session_manager.close()
