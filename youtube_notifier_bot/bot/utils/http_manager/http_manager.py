from asyncio import gather, sleep
from logging import getLogger
from typing import Coroutine, Dict, List

from httpx import AsyncClient, HTTPError, Response

from utils.decorators import rate_limit
from utils.http_manager.http_headers import ChromeHeadersBuilder

logger = getLogger(__name__)


class HTTPManager:
    TIMEOUT = 40

    FOLLOW_REDIRECTS = True
    HTTP2 = True

    HEADERS = {
        "authority": "www.youtube.com",
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/"
            "webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        # 'sec-ch-ua'
        # 'sec-ch-ua-full-version'
        # 'sec-ch-ua-full-version-list'
        # 'sec-ch-ua-arch'
        # 'sec-ch-ua-bitness'
        # 'sec-ch-ua-mobile'
        # 'sec-ch-ua-model'
        # 'sec-ch-ua-platform'
        # 'sec-ch-ua-platform-version'
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "service-worker-navigation-preload": "true",
        "upgrade-insecure-requests": "1",
        # 'user-agent'
    }

    @classmethod
    def __pre_request(cls) -> dict:
        """
        Формирует контекст для запроса
        """
        headers_builder = ChromeHeadersBuilder()
        headers_builder.headers.update(cls.HEADERS)

        return {"headers": headers_builder.headers}

    @classmethod
    async def __request(
        cls,
        method: str,
        url: str,
        client: AsyncClient,
        params: Dict | None = None,
        headers: Dict | None = None,
    ) -> Response | None:
        if headers is None:
            context = cls.__pre_request()
            headers = context["headers"]

        response = await client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            timeout=cls.TIMEOUT,
            follow_redirects=cls.FOLLOW_REDIRECTS,
        )
        if str(response.status_code).startswith("2"):
            return response

        else:
            logger.warning(
                'Response code %d: URL="%s" | %s',
                response.status_code,
                url,
                response.text,
            )

            return None

    @classmethod
    async def get(
        cls, url: str, params: Dict | None = None, headers: Dict | None = None
    ) -> Response | None:
        return await cls.request("GET", url, params, headers)

    @classmethod
    async def request(
        cls,
        method: str,
        url: str,
        params: Dict | None = None,
        headers: Dict | None = None,
    ) -> Response | None:
        result = None

        for _ in range(2):
            try:
                async with AsyncClient(
                    http2=cls.HTTP2,
                    timeout=cls.TIMEOUT * 2,
                    follow_redirects=cls.FOLLOW_REDIRECTS,
                ) as client:
                    result = await cls.__request(method, url, client, params, headers)
                    break

            except HTTPError as ex:
                logger.warning('HTTPError: URL="%s" | %s', url, ex)
                await sleep(2)

            except Exception as ex:
                logger.error(
                    'Request error: Type="%s" | URL="%s" | %s', type(ex), url, ex
                )
                await sleep(2)

        return result

    @classmethod
    @rate_limit(14)
    async def limit_url_gather(cls, tasks: List[Coroutine]) -> List[str | None]:
        return await gather(*tasks)  # noqa
