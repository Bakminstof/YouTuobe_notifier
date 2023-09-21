from typing import Any, Iterable, List, Sequence, Tuple

from sqlalchemy import Executable, Table, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import _AbstractLoad  # noqa


class CRUDMixin:
    table: Table | None = None

    default_limit: int = 100

    def __check_table(self) -> None:
        if not self.table:
            raise AttributeError(f"{self.__name__}.table is not set")

    def ordering(self, order_by: Executable | None) -> Executable:
        if isinstance(order_by, type(None)):
            return self.table.id  # type: ignore

        return order_by

    async def add_all(
        self,
        async_session: AsyncSession,
        instances: Iterable[Any],
    ) -> Iterable[Any]:
        async_session.add_all(instances)
        await async_session.commit()
        return instances

    async def add(
        self,
        async_session: AsyncSession,
        item: Any,
    ) -> Any:
        async_session.add(item)
        await async_session.commit()
        return item

    async def delete(
        self,
        async_session: AsyncSession,
        where: List | Tuple | None = None,
    ) -> bool:
        self.__check_table()

        stmt = delete(self.table)

        if where:
            stmt = stmt.where(*where)

        result = await async_session.execute(stmt)
        await async_session.commit()
        return bool(result.rowcount)

    async def update(
        self,
        async_session: AsyncSession,
        instances: List[dict],
    ) -> None:
        self.__check_table()

        await async_session.execute(update(self.table), instances)
        await async_session.commit()

    async def exists(
        self,
        async_session: AsyncSession,
        where: List | Tuple,
        options: List[_AbstractLoad] | None = None,
    ) -> bool:
        self.__check_table()

        if not options:
            options = []

        stmt = select(select(self.table).where(*where).options(*options).exists())

        result = await async_session.execute(stmt)
        await async_session.commit()
        return result.one()[0]

    async def get(
        self,
        async_session: AsyncSession,
        where: List[Any] | None = None,
        options: List[_AbstractLoad] | None = None,
        order_by: Any | None = None,
        limit: int = default_limit,
    ) -> Sequence[Any]:
        self.__check_table()
        stmt = select(self.table)
        if not options:
            options = []

        if where:
            stmt = stmt.where(*where)

        stmt = stmt.options(*options).order_by(self.ordering(order_by)).limit(limit)

        result = await async_session.scalars(stmt)
        result = result.unique().all()
        await async_session.commit()
        return result
