from logging import getLogger

from sqlalchemy import inspect

from db.core import async_engine
from db.declarative_base import Base
from db.schemas import TABLES
from loader import env_settings

logger = getLogger(__name__)


async def db_connect() -> None:
    """
    Проверка подключения к базе данных
    """
    logger.debug("Check connection")

    try:
        async with async_engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

            for table in TABLES:
                missing_tables = []

                if table.__tablename__ not in tables:
                    missing_tables.append(table.__tablename__)

                if missing_tables:
                    if env_settings.FORCE_INIT:
                        await conn.run_sync(Base.metadata.create_all)

                        logger.warning("Initialization database")
                    else:
                        exc_text = (
                            "Tables ({missing_tables}) not "
                            "in database tables ({tables})."
                        ).format(missing_tables=", ".join(missing_tables), tables=tables)

                        raise ValueError(exc_text)

        logger.debug("Connected to database")

    except ValueError as ex:
        logger.critical('Tables not found: Exception="%s" | %s', type(ex), ex)
        raise

    except Exception as ex:
        logger.critical('Can\'t connect to database: Exception="%s" | %s', type(ex), ex)
        raise
