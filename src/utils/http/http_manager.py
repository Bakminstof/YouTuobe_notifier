from asyncio import sleep
from copy import deepcopy
from logging import getLogger

from h2.exceptions import H2Error
from httpx import AsyncClient, HTTPError, Response

from core.settings import settings
from utils.http.http_headers import ChromeHeadersBuilder, Headers

logger = getLogger(__name__)


class HTTPManager:
    TIMEOUT: int = settings.requests_timeout * 2

    FOLLOW_REDIRECTS: bool = True
    HTTP2: bool = True

    HEADERS: dict[str, str] = {
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

    def __init__(self, request_hits: int = 2, hits_delay: int = 2) -> None:
        self.headers_builder: ChromeHeadersBuilder = ChromeHeadersBuilder()
        self.hits = request_hits
        self.hits_delay = hits_delay

    def __pre_request(self) -> dict:
        headers: Headers = Headers(deepcopy(self.HEADERS))
        return {"headers": self.headers_builder.randomize_headers(headers)}

    @staticmethod
    async def __request(
        method: str,
        url: str,
        client: AsyncClient,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | float = None,
        follow_redirects: bool = False,
    ) -> Response | None:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

        if str(response.status_code).startswith("2"):
            return response

        logger.warning(
            'Response code %d: URL="%s" | %s',
            response.status_code,
            url,
            response.text if len(response.text) < 50 else response.text[:50],
        )

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response | None:
        return await self.request("GET", url, params, headers)

    async def __hits(
        self,
        client: AsyncClient,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout=TIMEOUT,
        follow_redirects=FOLLOW_REDIRECTS,
    ) -> Response | None:
        for _ in range(self.hits):
            try:
                return await self.__request(
                    method=method,
                    url=url,
                    client=client,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    follow_redirects=follow_redirects,
                )

            except HTTPError as ex:
                logger.warning('HTTPError: URL="%s" | %s', url, ex)

                await sleep(self.hits_delay)

            except Exception as ex:
                logger.error(
                    'Request error: Type="%s" | URL="%s" | %s',
                    type(ex),
                    url,
                    ex,
                )

                await sleep(self.hits_delay)

    async def request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout=TIMEOUT,
        follow_redirects=FOLLOW_REDIRECTS,
    ) -> Response | None:
        if headers is None:
            context = self.__pre_request()
            headers = context["headers"]

        try:
            async with AsyncClient(
                http2=self.HTTP2,
                timeout=self.TIMEOUT,
                follow_redirects=self.FOLLOW_REDIRECTS,
            ) as client:
                return await self.__hits(
                    client,
                    method,
                    url,
                    params,
                    headers,
                    timeout,
                    follow_redirects,
                )
        except (H2Error, HTTPError) as ex:
            logger.warning('HTTPError: URL="%s" | %s', url, ex)
