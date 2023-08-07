from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.absolute()

# Environment
ENV_DIR = BASE_DIR / "environment"
# ENV_FILE = ENV_DIR / "dev.env"
ENV_FILE = ENV_DIR / "prod.env"

# Logging
LOGLEVEL = "DEBUG" if ENV_FILE.name == "dev.env" else "INFO"

LOGS_DIR = BASE_DIR / "logging_data" / "logs"

LOG_FORMAT = "%(levelname)s | %(name)s | %(asctime)s | %(lineno)s | <%(message)s>"
LOG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

LOGFILE_NAME = LOGS_DIR / "youtube_notifier.log"
LOGFILE_SIZE = 5 * 1024 * 1024  # 5 Mb
LOGFILE_COUNT = 10

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {"format": LOG_FORMAT, "datefmt": LOG_DATETIME_FORMAT},
        "colour": {
            "()": "logging_data.formatters.ColourFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": LOG_DATETIME_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOGLEVEL,
            "formatter": "colour",
        },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": LOGLEVEL,
            "filename": LOGFILE_NAME,
            "maxBytes": LOGFILE_SIZE,
            "backupCount": LOGFILE_COUNT,
            "formatter": "base",
        },
    },
    "root": {
        "level": LOGLEVEL,
        "handlers": ["console", "logfile"],
    },
}
