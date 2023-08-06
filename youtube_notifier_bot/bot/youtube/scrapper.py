from logging import getLogger
from re import findall, search, sub
from typing import List

logger = getLogger(__name__)


class Scrapper:
    @classmethod
    def find_content_urls(cls, channel_url: str, text: str) -> List[str] | List[None]:
        """
        Поиск ссылок на контент.
        """
        res = []

        urls = findall(r'/watch\?v=[^"\'&]*', text)

        if urls:
            res = urls

            logger.debug(
                'Found content URL\'s [%s]: Text="%s"',
                urls,
                text if len(text) < 20 else text[:20] + "...",
            )

        else:
            logger.info(
                'Content URL\'s not found: Channel URL="%s" Text="%s"',
                channel_url,
                text if len(text) < 200 else text[:199],
            )

        return res

    @classmethod
    def find_channel_url(cls, text: str) -> str | None:
        """
        Поиск URL канала.
        """
        target_span = search(r'(?=<span itemprop="author").*(?=</span>)', text)

        if target_span:
            url = search(r'link itemprop="url" href="[^"]*"', target_span.group())

            if url:
                url = sub(pattern="http", repl="https", string=url.group()[26:-1])

                logger.info('Found channel URL: Channel URL="%s"', url)

                return url

        logger.warning('URL not found: Text="%s"', text)

    @classmethod
    def find_channel_name(cls, text: str) -> str | None:
        """
        Поиск названия канала.
        """
        res = search(r'"name": "[^"]*"', text)

        if res:
            name = res.group()[9:-1]

            logger.debug('Found channel name: Channel name="%s"', name)

            return name

        else:
            logger.warning('Name not found: Text="%s"', text)

            return None
