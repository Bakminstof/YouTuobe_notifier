from loader import env_settings

SMILES = {
    "no": "\U0000274C",  # ❌
    "green_ok": "\U00002705",  # ✅
    "blue_ok": "\U00002611",  # ✅
    "hi": "\U0001F44B",  # 👋
    "r_arrow": "\U000027A1",  # ➡
    "hand": "\U0001F9BE",  # 🦾
    "sad_face": "\U0001F61E",  # 😞
    "stone_face": "\U0001F5FF",  # 🗿
    "orange_play": "\U000025B6",  # 🔽 ->
    "question": "\U00002753",  # ❓
    "stop": "\U0001F6A7",  # 🚧
    "medium_bs": "\U000025FC",  # ◼
    "block": "\U000026D4",  # ⛔
    "gear": "\U00002699",  # ⚙
}

MESSAGES = {
    "HOW_WORK": (
        "{question} Как бот работает?\n\n"
        "При появлении нового контента на канале бот "
        "присылает Вам уведомление".format(question=SMILES["question"])
    ),
    "WHAT_SEND": (
        "{question} Что отправить, чтобы подписаться "
        "на уведомления о новом контенте с канала?\n\n"
        "{blue_ok} Ссылку на сам канал. К примеру:\n"
        "{r_arrow} https://www.youtube.com/@twentyonepilots\n"
        "{r_arrow} https://www.youtube.com/channel/"
        "UCfM3zsQsOnfWNUppiycmBuw".format(
            question=SMILES["question"],
            blue_ok=SMILES["blue_ok"],
            r_arrow=SMILES["r_arrow"],
        )
    ),
    "INFO": (
        "{question} <b>Список доступных команд:</b>\n\n"
        "/start - <i>запуск бота</i>\n\n"
        "/channels - <i>список каналов</i>\n\n"
        "/info - <i>информация</i>\n\n"
        "{hand} <b><i>Техподдержка бота:</i></b> {sup}".format(
            question=SMILES["question"], hand=SMILES["hand"], sup=env_settings.SUPPORT
        )
    ),
}
