from asyncio import sleep
from logging import Logger, getLogger

from controllers import ChannelController, MessageController
from models.managers import ChannelManager


class Notifier:
    logger: Logger = getLogger(__name__)

    def __init__(
        self,
        delay: int | float = 300,
        cycle_name: str = "notify_cycle",
    ) -> None:
        self.message_controller: MessageController = MessageController()
        self.channel_controller: ChannelController = ChannelController()
        self.channel_manager: ChannelManager = ChannelManager()

        self.cycle_name = cycle_name
        self.cycle_delay = delay

        self.__run: bool = False

    def stop(self) -> None:
        self.__run = False

    async def start(self) -> None:
        self.__run = True

        self.logger.debug("Start `%s`", self.cycle_name)

        while self.__run:
            await self.channel_controller.load_from_db()
            await self.channel_controller.get_content(self.channel_controller.models_data)
            self.channel_controller.analise_found_content(
                self.channel_controller.models_data,
            )
            await self.channel_controller.send_and_update(
                self.channel_controller.models_data,
            )

            self.logger.debug("Sleeping %s sec.", self.cycle_delay)
            await sleep(self.cycle_delay)

        self.logger.debug("Stop `%s`", self.cycle_name)
