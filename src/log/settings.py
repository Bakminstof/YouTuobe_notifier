from functools import cached_property
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, computed_field, field_validator
from pydantic_core.core_schema import ValidationInfo


class LoggingSettings(BaseModel):
    sentry: str | None = None

    version: int = 1
    disable_existing_loggers: bool = False
    encoding: str = "UTF-8"

    loglevel: Literal[
        "NOTSET",
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    log_format: str = (
        "%(levelname)s | %(name)s | %(asctime)s | %(lineno)s | <%(message)s>"
    )

    log_datetime_format: str = "%Y-%m-%d %H:%M:%S"

    rotating_file_handler: bool = False
    logs_dir: str | Path = "logs"
    filename: str | Path = "app.log"
    max_bytes: int = 262_144_000
    backup_count: int = 20

    @field_validator("loglevel", mode="before")
    def loglevel_validator(
        cls,
        value: str,
        info: ValidationInfo,
        **kwargs,
    ) -> str:
        return value.upper()

    @field_validator("logs_dir", mode="before")
    def logs_dir_validator(
        cls,
        value: str,
        info: ValidationInfo,
        **kwargs,
    ) -> Path:
        value = Path(value)

        if value.root == "/":
            return value

        return Path(__file__).parent / value

    @field_validator("filename")
    def filename_validator(
        cls,
        value: str,
        info: ValidationInfo,
        **kwargs,
    ) -> Path:
        return info.data.get("logs_dir") / value

    @computed_field
    @cached_property
    def formatters(self) -> dict[str, Any]:
        return {
            "base": {
                "format": self.log_format,
                "datefmt": self.log_datetime_format,
            },
            "colour": {
                "()": "log.formatters.ColourFormatter",
                "fmt": self.log_format,
                "datefmt": self.log_datetime_format,
            },
        }

    @computed_field
    @cached_property
    def handlers(self) -> dict[str, Any]:
        return {
            "console": {
                "class": "logging.StreamHandler",
                "level": self.loglevel,
                "formatter": "colour",
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": self.loglevel,
                "formatter": "base",
                "filename": self.filename,
                "maxBytes": self.max_bytes,
                "encoding": self.encoding,
                "backupCount": self.backup_count,
            },
        }

    @computed_field
    @cached_property
    def dict_config(self) -> dict[str, Any]:
        handlers_names = [name for name in self.handlers.keys()]

        if not self.rotating_file_handler:
            handlers_names.remove("rotating_file")

        return {
            "version": self.version,
            "encoding": self.encoding,
            "disable_existing_loggers": self.disable_existing_loggers,
            "formatters": self.formatters,
            "handlers": self.handlers,
            "root": {
                "level": self.loglevel,
                "handlers": handlers_names,
            },
        }
