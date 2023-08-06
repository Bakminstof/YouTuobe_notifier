from asyncio import sleep
from functools import wraps
from typing import List


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


def rate_limit(limit_value: int = 0, delay: int | float = 1.2):
    """
    Декоратор для методов класса ограничения запросов в секунду.
    Если limit_value = 0, то ограничений нет.
    delay - промежуток между запросами. Задекорированная функция возвращает список результатов.
    :return: List[Any]
    """

    def __set_limit(func):
        @wraps(func)
        async def wrap(cls, args_list):
            if limit_value:
                parts = __split(args_list, limit_value)

            else:
                parts = args_list

            total_res = []

            for part in parts:
                res = await func(cls, part)

                if res:
                    total_res.extend(res)

                await sleep(delay)

            return total_res

        return wrap

    return __set_limit
