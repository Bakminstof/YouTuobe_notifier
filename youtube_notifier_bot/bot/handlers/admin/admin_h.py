from asyncio import gather

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy.orm import load_only

from config.msg_data import MESSAGES, SMILES
from db.core import async_session
from db.schemas import User
from filters import AdminFilter
from utils.message_manager import MessageManager
from utils.sender import Sender


async def admin_users(message: Message, state: FSMContext):
    chat_id = message.chat.id
    users = await User.get_all(
        async_session,
        options_set=[{load_only: (User.first_name, User.blocked, User.auth_timestamp)}],
        ordering=User.auth_timestamp.desc(),
        limit=20,
    )
    if users:
        mes = "\n\n".join(
            [
                "<b>{medium_bs} {username} {blocked}</b>\n"
                "<i>{auth_timestamp}</i>".format(
                    medium_bs=SMILES["medium_bs"],
                    username=user.first_name,
                    blocked=SMILES["block"] if user.blocked else "",
                    auth_timestamp=user.auth_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                )
                for user in users
            ]
        )

        await Sender.send_message(chat_id, mes)

    else:
        await Sender.send_message(chat_id, "Пользователей нет")


async def admin_check_users(message: Message, state: FSMContext):
    users = await User.get_all(
        async_session,
        options_set=[{load_only: User.telegram_id}],
        ordering=User.auth_timestamp.desc(),
    )

    chat_ids = [user.telegram_id for user in users]

    messages = await Sender.send_message_to_users(chat_ids, SMILES["hand"])

    tasks = [
        MessageManager.delete_message(chat_id, message.message_id)
        for chat_id, message in zip(chat_ids, messages)
        if message
    ]

    await gather(*tasks)

    await Sender.send_message(message.chat.id, SMILES["green_ok"])


async def admin_info(message: Message, state: FSMContext):
    chat_id = message.chat.id

    adm_info = (
        "{gear}\n\n"
        "/users - <i>список пользователей</i>\n\n"
        "/check_users - <i>проверить пользователей на блокировку</i>\n\n"
    ).format(gear=SMILES["gear"])

    await Sender.send_message(chat_id, MESSAGES["HOW_WORK"])
    await Sender.send_message(
        chat_id, MESSAGES["WHAT_SEND"], disable_web_page_preview=True
    )
    await Sender.send_message(chat_id, MESSAGES["INFO"])
    await Sender.send_message(chat_id, adm_info)


def register_admin(dp: Dispatcher) -> None:
    dp.register_message_handler(admin_info, AdminFilter(command="info"))
    dp.register_message_handler(admin_users, AdminFilter(command="users"))
    dp.register_message_handler(admin_check_users, AdminFilter(command="check_users"))
