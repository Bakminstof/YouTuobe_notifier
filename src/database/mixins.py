from typing import Any, AsyncGenerator, Sequence

from sqlalchemy import ScalarResult, Select, Table, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from core.schemas import PaginationModel, PaginationResultModel
from database.tps import created_at, updated_at

DEFAULT_LIMIT: int = 200
DEFAULT_ORDERING: str = "id"
DEFAULT_MAX_PAGES: int = 1000


class IDPKMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class ReprMixin:
    repr_col_num = 3
    repr_cols = tuple()

    def __repr__(self) -> str:
        cols = []

        for idx, col in enumerate(self.__table__.columns.keys()):  # type: ignore
            if self.repr_cols:
                if col in self.repr_cols:
                    cols.append(f"{col}={getattr(self, col)}")

            else:
                if idx < self.repr_col_num:
                    cols.append(f"{col}={getattr(self, col)}")

        return f"{self.__class__.__name__}({', '.join(cols)})"


class AuditMixin:
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class CRUDMixin:
    __table__: Any = None

    def __init__(self, async_session: AsyncSession) -> None:
        self.async_session = async_session

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ORM obj={self.__table__})"

    async def count(self, stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.async_session.scalar(count_stmt)
        await self.async_session.commit()
        return result

    async def update(self, instances: list[dict]) -> None:
        stmt = update(self.__table__)
        await self.async_session.execute(stmt, instances)
        await self.async_session.commit()

    async def create(self, instances: list[dict | Table]) -> Any:
        items = [
            self.__table__(**instance) if isinstance(instance, dict) else instance
            for instance in instances
        ]
        self.async_session.add_all(items)
        await self.async_session.commit()
        return items


class PaginationMixin(CRUDMixin):
    @classmethod
    def build_pagination(cls, limit: int, page: int, rows_count: int) -> PaginationModel:
        pages = rows_count // limit
        total_pages = pages if rows_count % limit == 0 else pages + 1

        pagination_dict = {
            "total": rows_count,
            "page": page,
            "per_page": limit,
            "total_pages": total_pages,
        }

        return PaginationModel.model_validate(pagination_dict)

    async def paginated_result(
        self,
        stmt: Any,
        page: int,
        limit: int | None = None,
        order_by: Any | None = None,
    ) -> PaginationResultModel:
        if limit is None:
            limit = DEFAULT_LIMIT

        if order_by is None:
            order_by = DEFAULT_ORDERING

        rows_count = await self.count(stmt)

        result = {}
        offset = (page - 1) * limit

        if rows_count > limit:
            result["pagination"] = self.build_pagination(limit, page, rows_count)

        result["data"] = await self.__limited_scalars(stmt, limit, offset, order_by)
        return PaginationResultModel.model_validate(result)

    async def __limited_scalars(
        self, stmt: Any, limit: int, offset: int, order_by: Any
    ) -> ScalarResult:
        result = await self.async_session.scalars(
            stmt.limit(limit).offset(offset).order_by(order_by)
        )
        await self.async_session.commit()
        return result

    @classmethod
    async def _get_paginated_result(
        cls, db_method, total_pages: int, **load_options
    ) -> AsyncGenerator[PaginationResultModel, None]:
        for page in range(2, total_pages + 1):
            load_options.update({"page": page})
            yield await db_method(**load_options)

    async def aiter_load(
        self,
        db_method,
        *,
        max_pages: int | None = DEFAULT_MAX_PAGES,
        per_page: int = DEFAULT_LIMIT,
        **load_options,
    ) -> AsyncGenerator[Sequence[Any], None]:  # Note: Количество подгружаемых строк (см)
        result = await db_method(**load_options)  # type: PaginationResultModel
        data = result.data.all()

        if not data:
            return

        yield data

        if not result.pagination:
            return

        if max_pages is None or result.pagination.total_pages <= max_pages:
            total_pages = result.pagination.total_pages

        else:
            total_pages = max_pages

        load_options["limit"] = per_page

        async for paginated_result in self._get_paginated_result(
            db_method, total_pages, **load_options
        ):
            yield paginated_result.data.all()
