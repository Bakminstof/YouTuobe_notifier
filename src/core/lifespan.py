from asyncio import get_running_loop
from logging import getLogger

from aiogram import Bot
from aiogram.types.bot_command import BotCommand

from apps.notifier.main import Notifier
from core.models import Smiles
from core.settings import settings
from database.utils import db, set_triggers
from routers.admin.utils import notify_admins
from utils.token_bucket import Limiter

logger = getLogger(__name__)


class Lifespan:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.notifier = Notifier(bot)

    async def _delete_webhook(self) -> None:
        deleted = await self.bot.delete_webhook()

        logger.info("Delete old webhook: %s", "OK" if deleted else "Fail")

    async def _set_webhook(self) -> None:
        await self.bot.set_webhook(
            url=settings.webhook.url(settings.bot_token),
            certificate=settings.webhook.public_key,
            secret_token=settings.secret_token,
        )

        logger.info(
            "Set webhook at: %s:%s",
            settings.webhook.host,
            settings.webhook.port,
        )

    async def set_bot_command(self) -> None:
        commands = [
            ["start", "Запустить бота"],
            ["channels", "Подписки"],
            ["info", "Информация"],
        ]
        await self.bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in commands
            ],
        )

        logger.info("Set bot commands: %s", commands)

    async def on_startup(self) -> None:
        Limiter.start()

        await db.init(
            settings.db.url,
            echo_sql=settings.db.echo_sql,
            echo_pool=settings.db.echo_pool,
            max_overflow=settings.db.max_overflow,
            pool_size=settings.db.pool_size,
        )
        await set_triggers()

        await self.set_bot_command()

        loop = get_running_loop()
        loop.create_task(self.notifier.start())

        webhook_info = await self.bot.get_webhook_info()

        if webhook_info.url:
            await self._delete_webhook()

        if settings.webhook.active:
            await self._set_webhook()

        logger.info(
            "Startup bot%s",
            ". Reverse proxy mod" if settings.webhook.reverse_proxy else "",
        )

        await notify_admins(
            self.bot,
            f"{Smiles.hand} <b><i>Startup bot"
            f"{'. Reverse proxy mod' if settings.webhook.reverse_proxy else ''}</i></b> "
            f"{Smiles.gear}",
        )

    async def on_shutdown(self) -> None:
        await notify_admins(
            self.bot,
            f"{Smiles.skull} <b><i>Grateful stopping bot...</i></b> {Smiles.skull}",
        )
        self.notifier.stop()
        await db.close()
        Limiter.stop()

        logger.info("Shutdown bot")
