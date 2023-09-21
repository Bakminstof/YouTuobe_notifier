from os import environ
from pathlib import Path
from ssl import PROTOCOL_TLSv1_2, SSLContext
from typing import Dict, List, Literal

from pydantic import field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

environ.setdefault("ENV_FILE", "dev.env")

BASE_DIR: Path = Path(__file__).parent

ENV_DIR: Path = BASE_DIR / "environment"
ENV_FILE: Path = ENV_DIR / environ["ENV_FILE"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    # Main
    DEBUG: bool = False

    BASE_DIR: Path = BASE_DIR

    # Bot
    BOT_TOKEN: str

    SKIP_UPDATES: bool = False

    ADMINS: List[int]

    SUPPORT: str | None = None

    # Webhook
    WEBHOOK: bool = False

    WEBHOOK_HOST: str | None = None
    WEBHOOK_PORT: int | None = None

    @field_validator(
        "WEBHOOK_HOST",
        "WEBHOOK_PORT",
        "TLS_DIR",
        "WEBHOOK_TLS_PRIVATE_KEY",
        "WEBHOOK_TLS_CERTIFICATE",
        mode="before",
    )
    def webhook_settings(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        if values.data.get("WEBHOOK"):
            if not value:
                raise ValueError(
                    f"If variable 'WEBHOOK' is True, `{values.field_name}` must be set."
                )

            return value

    @field_validator("WEBHOOK_HOST", mode="after")
    def webhook_host(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        return f"https://{value}" if value else None

    WEBHOOK_PATH: str | None = None
    WEBHOOK_URL: str | None = None

    @field_validator("WEBHOOK_PATH", mode="after")
    def webhook_path(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        return (
            f"/webhook/{values.data.get('BOT_TOKEN')}"
            if values.data.get("WEBHOOK")
            else None
        )

    @field_validator("WEBHOOK_URL", mode="after")
    def webhook_url(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        if values.data.get("WEBHOOK"):
            host = values.data.get("WEBHOOK_HOST")
            port = values.data.get("WEBHOOK_PORT")
            path = values.data.get("WEBHOOK_PATH")
            return f"{host}:{port}{path}"

    TLS_DIR: Path | None = None

    @field_validator("TLS_DIR", mode="after")
    def tls_dir(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        return BASE_DIR / value if value else None

    WEBHOOK_TLS_PRIVATE_KEY: Path | None = None
    WEBHOOK_TLS_CERTIFICATE: Path | None = None

    @field_validator("WEBHOOK_TLS_PRIVATE_KEY", mode="after")
    def webhook_tls_private_key(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        return values.data.get("TLS_DIR") / value if value else None

    @field_validator("WEBHOOK_TLS_CERTIFICATE", mode="after")
    def webhook_tls_certificate(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        return values.data.get("TLS_DIR") / value if value else None

    WEBAPP_HOST: str | None = None
    WEBAPP_PORT: int | None = None

    @field_validator("WEBAPP_HOST", "WEBAPP_PORT", mode="before")
    def debug_settings(
        cls,
        value: str | None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> str | None:
        if not values.data.get("DEBUG"):
            if not value:
                raise ValueError(
                    f"If debug mode is off, `{values.field_name}` must be set.",
                )

            return value

    TLS_CERTIFICATE: bytes | None = None
    TLS_CONTEXT: SSLContext | None = None

    @field_validator("TLS_CERTIFICATE", mode="before")
    def tls_certificate(
        cls,
        value: None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> bytes | None:
        if values.data.get("WEBHOOK"):
            cert: Path = values.data.get("WEBHOOK_TLS_CERTIFICATE")

            with cert.open(mode="rb") as file:
                return file.read()

    @field_validator("TLS_CONTEXT", mode="before")
    def tls_context(
        cls,
        value: None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> SSLContext | None:
        if values.data.get("WEBHOOK"):
            tls_context = SSLContext(PROTOCOL_TLSv1_2)

            certfile: Path = values.data.get("WEBHOOK_TLS_CERTIFICATE")
            keyfile: Path = values.data.get("WEBHOOK_TLS_PRIVATE_KEY")

            tls_context.load_cert_chain(
                certfile=certfile,
                keyfile=keyfile,
            )

            return tls_context

    # Database
    DB_DRIVER: str

    DB_NAME: str

    DB_HOST: str | None = None
    DB_PORT: int | None = None

    DB_USER: str | None = None
    DB_PASS: str | None = None

    ECHO_SQL: bool = DEBUG

    FORCE_INIT: bool = False

    DB_URL: URL | None = None

    @field_validator("DB_URL")
    def db_url(
        cls,
        value: None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> URL:
        return URL.create(
            values.data.get("DB_DRIVER"),
            values.data.get("DB_USER"),
            values.data.get("DB_PASS"),
            values.data.get("DB_HOST"),
            values.data.get("DB_PORT"),
            values.data.get("DB_NAME"),
        )

    # Logging
    SENTRY: str | None = None

    LOGLEVEL: Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    LOG_FORMAT: str

    LOG_DATETIME_FORMAT: str

    LOGS_DIR: Path = "logs"

    @field_validator("LOGS_DIR", mode="before")
    def logs_dir(cls, value: str, values: FieldValidationInfo, **kwargs) -> Path:  # noqa
        return values.data.get("BASE_DIR") / "logging_data" / value

    LOGFILE_NAME: Path = "bot.log"

    @field_validator("LOGFILE_NAME", mode="before")
    def logfile_name(
        cls,
        value: str,
        values: FieldValidationInfo,
        **kwargs,
    ) -> Path:
        return values.data.get("LOGS_DIR") / value

    LOGFILE_SIZE: int
    LOGFILE_COUNT: int

    LOGGING: Dict | None = None

    @field_validator("LOGGING")
    def logging(
        cls,
        value: None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> Dict:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "base": {
                    "format": values.data.get("LOG_FORMAT"),
                    "datefmt": values.data.get("LOG_DATETIME_FORMAT"),
                },
                "colour": {
                    "()": "logging_data.formatters.ColourFormatter",
                    "fmt": values.data.get("LOG_FORMAT"),
                    "datefmt": values.data.get("LOG_DATETIME_FORMAT"),
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": values.data.get("LOGLEVEL"),
                    "formatter": "colour",
                },
                "logfile": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": values.data.get("LOGLEVEL"),
                    "filename": values.data.get("LOGFILE_NAME"),
                    "maxBytes": values.data.get("LOGFILE_SIZE"),
                    "backupCount": values.data.get("LOGFILE_COUNT"),
                    "formatter": "base",
                },
            },
            "root": {
                "level": values.data.get("LOGLEVEL"),
                "handlers": ["console", "logfile"],
            },
        }

    SMILES: Dict = {
        "no": "\U0000274C",  # ~            ❌
        "green_ok": "\U00002705",  # ~      ✅
        "blue_ok": "\U00002611",  # ~       ✅
        "hi": "\U0001F44B",  # ~            👋
        "r_arrow": "\U000027A1",  # ~       ➡
        "hand": "\U0001F9BE",  # ~          🦾
        "sad_face": "\U0001F61E",  # ~      😞
        "stone_face": "\U0001F5FF",  # ~    🗿
        "orange_play": "\U000025B6",  # ~   🔽 ->
        "question": "\U00002753",  # ~      ❓
        "stop": "\U0001F6A7",  # ~          🚧
        "medium_bs": "\U000025FC",  # ~     ◼
        "block": "\U000026D4",  # ~         ⛔
        "gear": "\U00002699",  # ~          ⚙
    }

    MESSAGES: Dict[str, str] | None = None

    @field_validator("MESSAGES", mode="before")
    def messages(
        cls,
        value: None,
        values: FieldValidationInfo,
        **kwargs,
    ) -> Dict[str, str]:
        question = values.data.get("SMILES")["question"]
        blue_ok = values.data.get("SMILES")["blue_ok"]
        r_arrow = values.data.get("SMILES")["r_arrow"]
        hand = values.data.get("SMILES")["hand"]
        support = values.data.get("SUPPORT")

        return {
            "HOW_WORK": (
                f"{question} Как бот работает?\n\n"
                "При появлении нового контента на канале бот "
                "присылает Вам уведомление"
            ),
            "WHAT_SEND": (
                f"{question} Что отправить, чтобы подписаться "
                "на уведомления о новом контенте с канала?\n\n"
                f"{blue_ok} Ссылку на сам канал. К примеру:\n"
                f"{r_arrow} https://www.youtube.com/@twentyonepilots\n"
                f"{r_arrow} https://www.youtube.com/channel/"
                "UCfM3zsQsOnfWNUppiycmBuw"
            ),
            "INFO": (
                f"{question} <b>Список доступных команд:</b>\n\n"
                "/start - <i>запуск бота</i>\n\n"
                "/channels - <i>список каналов</i>\n\n"
                "/info - <i>информация</i>\n\n"
                f"{hand} <b><i>Техподдержка бота:</i></b> {support}"
            ),
        }


settings: Settings = Settings()
