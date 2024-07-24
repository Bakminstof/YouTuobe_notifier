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
