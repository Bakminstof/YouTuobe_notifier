from logging import Logger, getLogger
from re import findall, search
from typing import List


class Finder:
    logger: Logger = getLogger(__name__)
    log_text_max_len: int = 200

    def __compress_log_text(self, text: str) -> str:
        return (
            text if len(text) < self.log_text_max_len else text[: self.log_text_max_len]
        )

    def find_channel_url(self, page: str, from_url: str | None = None) -> str | None:
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

        self.logger.warning(
            'Channels URL not found: URL="%s" | Text="%s"',
            from_url,
            self.__compress_log_text(page),
        )

    def find_canonical_url(self, page: str, from_url: str | None = None) -> str | None:
        """
        Поиск каноничной ссылки страницы.
        """
        result = search('(?<=<link rel="canonical" href=")[^"]+(?<!">)', page)
        if result:
            return result.group()

        self.logger.warning(
            'Canonical URL not found: URL="%s" | Text="%s"',
            from_url,
            self.__compress_log_text(page),
        )

    def find_original_url(self, page: str, from_url: str | None = None) -> str | None:
        """
        Поиск оригинального URL.
        """
        result = search('(?<="originalUrl":")[^"]+(?<!")', page)
        if result:
            return result.group()

        self.logger.warning(
            'Original URL not found: URL="%s" | Text="%s"',
            from_url,
            self.__compress_log_text(page),
        )

    def find_channel_name(
        self,
        channel_page: str,
        from_url: str | None = None,
    ) -> str | None:
        """
        Поиск названия канала.
        """
        result = search('(?<="name": ")[^"]*(?<!")', channel_page)
        if result:
            return result.group()

        self.logger.warning(
            'Channel name not found: URL="%s" | Text="%s"',
            from_url,
            self.__compress_log_text(channel_page),
        )

    def find_content_urls(
        self,
        channel_page: str,
        from_url: str | None = None,
    ) -> List[str]:
        """
        Поиск ссылок на контент.
        """
        urls = findall(r"/watch\?v=[^\"'\\&?]{1,11}", channel_page)

        if not urls:
            self.logger.warning(
                'Content URL\'s not found: URL="%s" | Text="%s"',
                from_url,
                self.__compress_log_text(channel_page),
            )

        return urls
