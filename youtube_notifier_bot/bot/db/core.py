from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession

from loader import env_settings

db_url_object = URL.create(
    drivername=env_settings.DB_DRIVER,
    database=env_settings.DB_NAME,
    username=env_settings.DB_USER,
    password=env_settings.DB_PASS,
    host=env_settings.DB_HOST,
    port=env_settings.DB_PORT,
)

connect_args = {}

async_engine = create_async_engine(
    url=db_url_object, echo=env_settings.ECHO_SQL, connect_args=connect_args
)

async_session = async_sessionmaker(
    bind=async_engine, expire_on_commit=False, autoflush=True, class_=AsyncSession
)
