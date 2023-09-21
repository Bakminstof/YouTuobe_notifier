from asyncio import gather, sleep
from typing import Any, Awaitable, List


def __split(data: List, n: int) -> List[List]:
    """
    Делит список на равные части по n объектов в каждом.
    """
    sections = []

    if len(data) > n:
        while data:
            part = data[:n]
            data = data[n:]
            sections.append(part)

    else:
        sections.append(data)

    return sections


async def limit_gather(
    tasks: List[Awaitable],
    part_len: int = 0,
    delay: int | float = 1.2,
) -> List[object]:
    if part_len:
        parts = __split(tasks, part_len)
    else:
        parts = [tasks]

    result = []

    for part in parts:
        res = await gather(*part)

        if res:
            result.extend(res)

        if len(parts) != 1:
            await sleep(delay)

    return result
