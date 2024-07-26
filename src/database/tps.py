from datetime import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import mapped_column


created_at = Annotated[
    datetime,
    mapped_column(
        server_default=func.now(),
    ),
]

updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=func.now(),
    ),
]

str_200 = Annotated[str, 200]
