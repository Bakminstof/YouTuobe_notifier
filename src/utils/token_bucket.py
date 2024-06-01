from asyncio import Lock, get_running_loop, sleep
from functools import wraps
from logging import getLogger

from core.settings import settings

logger = getLogger(__name__)


class Bucket:
    __slots__ = ("name", "max_tokens", "rate", "__tokens", "__started", "__lock")

    def __init__(
        self,
        name: str,
        rate: int | float = 10.0,
        max_tokens: int | None = None,
    ) -> None:
        self.name = name
        self.rate = rate

        if isinstance(max_tokens, (int, float)):
            self.max_tokens = max_tokens
        else:
            self.max_tokens = int(rate)

        self.__started = False
        self.__tokens = 0
        self.__lock = Lock()

    @property
    def started(self) -> bool:
        return self.__started

    def start(self) -> None:
        self.__started = True

        loop = get_running_loop()
        loop.create_task(self._auto_replenish())  # noqa

        logger.debug(f'Bucket started. Bucket="{self.name}"')

    def stop(self) -> None:
        self.__started = False

        logger.debug(f'Bucket stopped. Bucket="{self.name}"')

    async def _auto_replenish(self) -> None:
        while self.__started:
            if self.__tokens < self.max_tokens:
                async with self.__lock:
                    self.__tokens += 1

            await sleep(1 / self.rate)

    async def consume(self, tokens: int) -> bool:
        if self.__tokens >= tokens:
            async with self.__lock:
                self.__tokens -= tokens
            return True
        return False


class Limiter:
    limits: dict[str, int] = {"Default": 10}
    limits.update(settings.rate_limits)

    groups: dict[str, Bucket] = {}

    @classmethod
    def start(cls) -> None:
        logger.info("Startup buckets")

        for name, rate in cls.limits.items():
            bucket = Bucket(name, rate)
            cls.groups[name] = bucket
            bucket.start()

    @classmethod
    def stop(cls) -> None:
        logger.info("Shutdown buckets")

        for bucket in cls.groups.values():
            bucket.stop()


class rate_limit:  # noqa
    __slots__ = ("group_name", "weight")

    def __init__(self, group_name: str = "Default", weight: int = 1) -> None:
        if group_name not in Limiter.limits.keys():
            raise ValueError(f"Group `{group_name}` not found")

        self.group_name = group_name
        self.weight = weight

    def __call__(self, func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            bucket = Limiter.groups[self.group_name]

            while bucket.started:
                if await bucket.consume(self.weight):
                    return await func(*args, **kwargs)

                await sleep(1 / bucket.rate)

        return async_wrapper
