from sqlalchemy import String, MetaData
from sqlalchemy.orm import DeclarativeBase

from core.settings import settings
from database.mixins import ReprMixin, IDPKMixin
from database.tps import str_200


class Base(DeclarativeBase, ReprMixin, IDPKMixin):
    __abstract__ = True

    type_annotation_map = {str_200: String(200)}

    metadata = MetaData(naming_convention=settings.db.naming_convention)
