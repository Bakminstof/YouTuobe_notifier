from logging import getLogger
from re import findall, search
from typing import List

from utils.common import strip_text

logger = getLogger(__name__)


def find_channel_url(page: str, from_url: str | None = None) -> str | None:
    """
    Поиск URL канала на странице видео, стрима или главной странице канала.
    """
    target_span = search('(?<=<span itemprop="author").*(?<!</span>)', page)

    if target_span:
        url = search(
            '(?<=link itemprop="url" href=")[^"]+(?<!")',
            target_span.group(),
        )

        return url.group() if url else None

    logger.warning(
        'Channels URL not found: URL="%s" | Text="%s"',
        from_url,
        strip_text(page),
    )

    return None


def find_canonical_url(page: str, from_url: str | None = None) -> str | None:
    """
    Поиск каноничной ссылки страницы.
    """
    result = search('(?<=<link rel="canonical" href=")[^"]+(?<!">)', page)
    if result:
        return result.group()

    logger.warning(
        'Canonical URL not found: URL="%s" | Text="%s"',
        from_url,
        strip_text(page),
    )
    return None


def find_original_url(page: str, from_url: str | None = None) -> str | None:
    """
    Поиск оригинального URL.
    """
    result = search('(?<="originalUrl":")[^"]+(?<!")', page)
    if result:
        return result.group()

    logger.warning(
        'Original URL not found: URL="%s" | Text="%s"',
        from_url,
        strip_text(page),
    )
    return None


def find_channel_name(
    channel_page: str,
    from_url: str | None = None,
) -> str | None:
    """
    Поиск названия канала.
    """
    result = search('(?<="name": ")[^"]*(?<!")', channel_page)
    if result:
        return result.group()

    logger.warning(
        'Channel name not found: URL="%s" | Text="%s"',
        from_url,
        strip_text(channel_page),
    )
    return None


def find_content_urls(
    channel_page: str,
    from_url: str | None = None,
) -> List[str]:
    """
    Поиск ссылок на контент.
    """
    urls = findall(r"/watch\?v=[^\"'\\&?]{1,11}", channel_page)

    if not urls:
        logger.warning(
            'Content URL\'s not found: URL="%s" | Text="%s"',
            from_url,
            strip_text(channel_page),
        )

    return urls
