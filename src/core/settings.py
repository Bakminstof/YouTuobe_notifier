from functools import cached_property
from os import environ
from pathlib import Path

from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from pydantic import BaseModel, ConfigDict, computed_field, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from log.config import LoggingSettings

BASE_DIR = Path(__file__).parent.parent
ENV_DIR = BASE_DIR / "env"

environ.setdefault(
    "ENV_FILE",
    (ENV_DIR / "dev.env").absolute().as_posix(),
)


class DBSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    drivername: str

    user: str | None = None
    password: str | None = None

    host: str | None = None
    port: int | str | None = None

    name: str

    echo_sql: bool = False
    echo_pool: bool = False
    max_overflow: int = 10
    pool_size: int = 5

    naming_convention: dict = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @field_validator("name")
    def db_name_validator(
        cls,
        value: str,
        info: ValidationInfo,
        **kwargs,
    ) -> str:
        if "sqlite" in info.data.get("drivername"):
            return (BASE_DIR.parent / "db" / value).absolute().as_posix()

    @field_validator(
        "user",
        "password",
        "host",
        "port",
    )
    def db_settings_validator(
        cls,
        value: str | int | None,
        info: ValidationInfo,
        **kwargs,
    ) -> str | int | None:
        if not value:
            if "postgresql" in info.data.get("drivername"):
                raise ValueError(f"`{info.field_name}` must be `set")

            return None

        if info.field_name == "port":
            return int(value)

        return value

    @computed_field
    @cached_property
    def url(self) -> URL:
        return URL.create(
            drivername=self.drivername,
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


class WebhookSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    active: bool = False

    host: str | None = None
    port: int | str | None = None

    web_server_host: str | None = None
    web_server_port: int | None = None

    reverse_proxy: bool = False

    @computed_field
    @cached_property
    def public_key(cls) -> FSInputFile | None:
        if cls.active:
            return FSInputFile(BASE_DIR.parent / "certs" / "notif-bot-public.pem")
        return None

    @computed_field
    @cached_property
    def private_key(cls) -> FSInputFile | None:
        if cls.active:
            return FSInputFile(BASE_DIR.parent / "certs" / "notif-bot-private.pem")
        return None

    @field_validator(
        "web_server_host",
        "web_server_port",
        "host",
        "port",
        mode="before",
        check_fields=True,
    )
    def settings_validator(
        cls,
        value: int | str | None,
        info: ValidationInfo,
        **kwargs,
    ) -> int | str | None:
        if info.data.get("active") and (not value):
            raise ValueError(f"If 'active' is True, `{info.field_name}` must be set.")

        if "port" in info.field_name and value:
            return int(value)

        return value if value else None

    @field_validator("host")
    def host_validator(
        cls,
        value: str | None,
        info: ValidationInfo,
        **kwargs,
    ) -> str | None:
        if value:
            return f"https://{value}"
        return None

    @classmethod
    def path(cls, bot_token: str) -> str:
        return f"/webhook/{bot_token}"

    def url(self, bot_token: str) -> str:
        return f"{self.host}:{self.port}{self.path(bot_token)}"


class BotMessageUtils(BaseModel):
    smiles: dict = {
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
        "gear": "\U00002699",  # ~          ⚙
        "block": "\U000026D4",  # ~         ⛔
        "skull": "\U0001F480",  # ~         💀
        "ban": "\U0001F6D1",  # ~           🛑
        "lifebuoy": "\U0001F6DF",  # ~      🛟
    }

    messages: dict = {
        "how_work": (
            f"{smiles['question']} Как бот работает?\n\n"
            "При появлении нового контента на канале бот "
            "присылает Вам уведомление"
        ),
        "what_send": (
            f"{smiles['question']} Что отправить, чтобы подписаться "
            "на уведомления о новом контенте с канала?\n\n"
            f"{smiles['blue_ok']} Ссылку на сам канал. К примеру:\n"
            f"{smiles['r_arrow']} https://www.youtube.com/@twentyonepilots\n"
            f"{smiles['r_arrow']} https://www.youtube.com/channel/UCfM3zsQsOnfWNUppiycmBuw"
        ),
        "info": (
            f"{smiles['question']} <b>Список доступных команд:</b>\n\n"
            "/start - <i>запуск бота</i>\n\n"
            "/channels - <i>список каналов</i>\n\n"
            "/info - <i>информация</i>\n\n"
        ),
        "admin": (
            f"{smiles['gear']} <b>Команды администрирования:</b> {smiles['gear']}\n\n"
            "/users - <i>список пользователей</i>\n\n"
        ),
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="app.",
        env_file=(f"{ENV_DIR / '.env.template'}", environ["ENV_FILE"]),
        case_sensitive=False,
        env_nested_delimiter=".",
        env_file_encoding="UTF-8",
    )

    # ======================================|Main|====================================== #
    debug: bool

    bot_token: str
    secret_token: str | None = None

    admins: list[int]
    parse_mod: str = ParseMode.HTML

    bot_msg_utils: BotMessageUtils = BotMessageUtils()

    support: str | None = None

    rate_limits: dict[str, int] = {"YouTube": 7, "Telegram": 35}

    requests_timeout: int = 10

    # ====================================|Webhook|===================================== #
    webhook: WebhookSettings
    # ====================================|Database|==================================== #
    db: DBSettings
    # ====================================|Logging|===================================== #
    logging: LoggingSettings


settings = Settings()
