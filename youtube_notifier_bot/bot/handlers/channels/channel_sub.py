from logging import getLogger

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.exc import IntegrityError

from config.msg_data import SMILES
from db.core import async_session
from db.schemas import Association
from keyboards.inline import callback_channel
from utils.message_manager import MessageManager

logger = getLogger(__name__)


async def sub(call: CallbackQuery, state: FSMContext):
    pack = await MessageManager.load_channel_msg_data(call, state)

    if pack:
        channel_msg, current_channel, user, limit = pack

        if limit:
            sub_text = "\n\n{stop} У вас лимит подписок {stop}".format(
                stop=SMILES["stop"]
            )
            await MessageManager.edit_message(channel_msg, SMILES["no"], sub_text)

        else:
            await MessageManager.edit_message(channel_msg, SMILES["green_ok"])

            try:  # spam protection
                await Association.add_association(user, current_channel, async_session)
            except IntegrityError:
                pass

            logger.debug(
                'Subscription: User="%s" -> Channel="%s"',
                user.first_name,
                current_channel.name,
            )


async def unsub(call: CallbackQuery, state: FSMContext):
    pack = await MessageManager.load_channel_msg_data(call, state)

    if pack:
        channel_msg, current_channel, user, _ = pack

        await MessageManager.edit_message(channel_msg, SMILES["no"])
        await Association.delete(user, current_channel, async_session)

        logger.debug(
            'Unsubscription: User="%s" X Channel="%s"',
            user.first_name,
            current_channel.name,
        )


def register_sub_channel(dp: Dispatcher) -> None:
    dp.register_callback_query_handler(unsub, callback_channel.filter(action="unsub"))
    dp.register_callback_query_handler(sub, callback_channel.filter(action="sub"))
