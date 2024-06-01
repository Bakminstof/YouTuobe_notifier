from logging import getLogger
from re import search

from apps.notifier.schemas import ContentType
from utils.finder import find_channel_url, find_content_urls
from utils.http import HTTPManager
from utils.token_bucket import rate_limit

logger = getLogger(__name__)


@rate_limit("YouTube")
async def _load_page(url: str) -> str | None:
    http_manager = HTTPManager()
    response = await http_manager.get(url)

    if response:
        return response.text

    logger.warning('Can\'t load page: URL="%s"', url)


async def get_channel_page(raw_url: str) -> str | None:
    if search(
        r"(?:/watch|videos|streams|shorts|playlists|community|channels|about|\?).+",
        raw_url,
    ):
        channel_url = await __get_channel_url_by_content_url(raw_url)

        if not channel_url:
            return

        return await _load_page(url=channel_url)

    channel_page = await _load_page(url=raw_url)

    if channel_page:
        return channel_page


async def __get_channel_url_by_content_url(content_url: str) -> str | None:
    """Поиск URL канала по URL контента"""
    content_page = await _load_page(url=content_url)
    if content_page is None:
        return

    return find_channel_url(content_page, content_url)


async def get_content_urls(channel_url: str, content_type: ContentType) -> set[str]:
    """Получение множества URL контента"""
    url = f"{channel_url}/{content_type}"
    content_page = await _load_page(url=url) or ""
    return set(find_content_urls(content_page, url))
