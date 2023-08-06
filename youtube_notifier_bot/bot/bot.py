from aiogram import executor

from handlers import register_all
from loader import dp, env_settings, ssl_context
from utils.event_manager import EventHandler


def start() -> None:
    register_all(dp)  # Register all handlers

    if env_settings.WEBHOOK:
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=env_settings.WEBHOOK_PATH,
            on_startup=EventHandler.on_startup,
            on_shutdown=EventHandler.on_shutdown,
            skip_updates=env_settings.SKIP_UPDATES,
            host=env_settings.WEBAPP_HOST,
            port=env_settings.WEBAPP_PORT,
            ssl_context=ssl_context,
        )

    else:
        executor.start_polling(
            dispatcher=dp,
            on_startup=EventHandler.on_startup,
            on_shutdown=EventHandler.on_shutdown,
            skip_updates=env_settings.SKIP_UPDATES,
        )


if __name__ == "__main__":
    start()
