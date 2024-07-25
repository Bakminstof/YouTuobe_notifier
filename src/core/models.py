from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ScalarResult


class PaginationModel(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginationResultModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: ScalarResult
    pagination: PaginationModel | None = None


class Smiles(StrEnum):
    no = "\U0000274C"  # ~            ❌
    green_ok = "\U00002705"  # ~      ✅
    blue_ok = "\U00002611"  # ~       ✅
    hi = "\U0001F44B"  # ~            👋
    r_arrow = "\U000027A1"  # ~       ➡
    hand = "\U0001F9BE"  # ~          🦾
    sad_face = "\U0001F61E"  # ~      😞
    stone_face = "\U0001F5FF"  # ~    🗿
    orange_play = "\U000025B6"  # ~   🔽 ->
    question = "\U00002753"  # ~      ❓
    stop = "\U0001F6A7"  # ~          🚧
    medium_bs = "\U000025FC"  # ~     ◼
    gear = "\U00002699"  # ~          ⚙
    block = "\U000026D4"  # ~         ⛔
    skull = "\U0001F480"  # ~         💀
    ban = "\U0001F6D1"  # ~           🛑
    lifebuoy = "\U0001F6DF"  # ~      🛟


class UtilMessages(StrEnum):
    how_work = (
        f"{Smiles.question} Как бот работает?\n\n"
        "При появлении нового контента на канале бот "
        "присылает Вам уведомление"
    )

    what_send = (
        f"{Smiles.question} Что отправить, чтобы подписаться "
        "на уведомления о новом контенте с канала?\n\n"
        f"{Smiles.blue_ok} Ссылку на сам канал. К примеру:\n"
        f"{Smiles.r_arrow} https://www.youtube.com/@twentyonepilots\n"
        f"{Smiles.r_arrow} https://www.youtube.com/channel/UCfM3zsQsOnfWNUppiycmBuw"
    )

    info = (
        f"{Smiles.question} <b>Список доступных команд:</b>\n\n"
        "/start - <i>запуск бота</i>\n\n"
        "/channels - <i>список каналов</i>\n\n"
        "/info - <i>информация</i>\n\n"
    )

    admin_commands = (
        f"{Smiles.gear} <b>Команды администрирования:</b> {Smiles.gear}\n\n"
        "/users - <i>список пользователей</i>\n\n"
    )
