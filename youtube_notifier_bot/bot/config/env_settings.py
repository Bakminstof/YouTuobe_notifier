from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings

from settings import BASE_DIR, ENV_FILE


class ENVSettings(BaseSettings):
    # Main
    DEBUG: bool = False

    # Bot
    BOT_TOKEN: str

    SKIP_UPDATES: bool = False

    ADMINS: List[int]

    # Logging
    SENTRY: str | None = None

    # Support URL
    SUPPORT: str | None = None

    # Webhook
    WEBHOOK: bool = False

    WEBHOOK_HOST: str | None = None
    WEBHOOK_PORT: int | None = None

    @field_validator(
        "WEBHOOK_HOST",
        "WEBHOOK_PORT",
        "TSL_DIR",
        "WEBHOOK_TSL_PRIVATE_KEY",
        "WEBHOOK_TSL_CERTIFICATE",
        mode="before",
    )
    def webhook_settings(cls, v, values, **kwargs):  # noqa
        if values.data.get("WEBHOOK"):
            if v:
                return v
            else:
                raise ValueError(
                    "If variable 'WEBHOOK' is True, `{}` must be set.".format(
                        values.field_name
                    )
                )
        else:
            return None

    @field_validator("WEBHOOK_HOST", mode="after")
    def webhook_host(cls, v, values, **kwargs):  # noqa
        return "https://{}".format(v) if v else None

    WEBHOOK_PATH: str | None = None

    @field_validator("WEBHOOK_PATH", mode="after")
    def webhook_path(cls, v, values, **kwargs):  # noqa
        return (
            "/webhook/{}".format(values.data.get("BOT_TOKEN"))
            if values.data.get("WEBHOOK")
            else None
        )

    WEBHOOK_URL: str | None = None

    @field_validator("WEBHOOK_URL", mode="after")
    def webhook_url(cls, v, values, **kwargs):  # noqa
        if values.data.get("WEBHOOK"):
            return "{}:{}{}".format(
                values.data.get("WEBHOOK_HOST"),
                values.data.get("WEBHOOK_PORT"),
                values.data.get("WEBHOOK_PATH"),
            )
        else:
            return None

    TSL_DIR: Path | None = None

    @field_validator("TSL_DIR", mode="after")
    def tsl_dir(cls, v, values, **kwargs):  # noqa
        return BASE_DIR / v if v else None

    WEBHOOK_TSL_PRIVATE_KEY: Path | None = None

    @field_validator("WEBHOOK_TSL_PRIVATE_KEY", mode="after")
    def webhook_tsl_private_key(cls, v, values, **kwargs):  # noqa
        return values.data.get("TSL_DIR") / v if v else None

    WEBHOOK_TSL_CERTIFICATE: Path | None = None

    @field_validator("WEBHOOK_TSL_CERTIFICATE", mode="after")
    def webhook_tsl_certificate(cls, v, values, **kwargs):  # noqa
        return values.data.get("TSL_DIR") / v if v else None

    # Webserver
    WEBAPP_HOST: str | None = None
    WEBAPP_PORT: int | None = None

    @field_validator("WEBAPP_HOST", "WEBAPP_PORT", mode="before")
    def debug_settings(cls, v, values, **kwargs):  # noqa
        if not values.data.get("DEBUG"):
            if v:
                return v
            else:
                raise ValueError(
                    "If debug mode is off, `{}` must be set.".format(values.field_name)
                )
        else:
            return None

    # Database
    DB_DRIVER: str

    DB_NAME: str

    DB_HOST: str | None = None
    DB_PORT: int | None = None

    DB_USER: str | None = None
    DB_PASS: str | None = None

    ECHO_SQL: bool = DEBUG

    FORCE_INIT: bool = False

    class Config:
        env_file = ENV_FILE
