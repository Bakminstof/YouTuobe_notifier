from copy import deepcopy
from random import choice
from typing import Dict, List, Tuple


class Headers:
    def __init__(self, options: Dict[str, str] | None = None) -> None:
        self.options = options or {}

        self.chrome_version: Tuple[str, str] | None = None

        # sec-ch-ua
        self.sec_ch_ua_conf: Dict | None = None

        self.sec_ch_ua: str | None = None
        self.sec_ch_ua_full_version: str | None = None
        self.sec_ch_ua_full_version_list: str | None = None
        self.sec_ch_ua_platform: str | None = None
        self.sec_ch_ua_platform_version: str | None = None
        self.sec_ch_ua_arch: str | None = None
        self.sec_ch_ua_bitness: str | None = None
        self.sec_ch_ua_mobile: str | None = None
        self.sec_ch_ua_model: str | None = None

        # user-agent
        self.user_agent: str | None = None

    @property
    def headers(self) -> Dict[str, str]:
        return self.options


class ChromeHeadersBuilder:
    CHROME_VERSIONS: Dict[str, List[str]] = {
        "100": [
            "100.0.4896.127",  # ~  04-2022
            "100.0.4896.143",  # ~  04-2022
        ],
        "101": [
            "101.0.4951.41",  # ~   04-2022
            "101.0.4951.67",  # ~   05-2022
        ],
        "102": [
            "102.0.5005.61",  # ~   05-2022
            "102.0.5005.62",  # ~   05-2022
            "102.0.5005.63",  # ~   05-2022
            "102.0.5005.134",  # ~  06-2022
            "102.0.5005.167",  # ~  07-2022
        ],
        "103": [
            "103.0.5060.53",  # ~   06-2022
            "103.0.5060.66",  # ~   06-2022
            "103.0.5060.134",  # ~  07-2022
        ],
        "104": [
            "104.0.5112.101",  # ~  08-2022
            "104.0.5112.111",  # ~  08-2022
        ],
        "105": [
            "105.0.5195.52",  # ~   08-2022
        ],
        "106": [
            "106.0.5249.61",  # ~   09-2022
            "106.0.5249.91",  # ~   09-2022
            "106.0.5249.165",  # ~  10-2022
            "106.0.5249.168",  # ~  10-2022
            "106.0.5249.181",  # ~  11-2022
            "106.0.5249.199",  # ~  11-2022
        ],
        "107": [
            "107.0.5304.62",  # ~   10-2022
            "107.0.5304.87",  # ~   10-2022
            "107.0.5304.110",  # ~  11-2022
            "107.0.5304.121",  # ~  11-2022
        ],
        "108": [
            "108.0.5359.71",  # ~   11-2022
            "108.0.5359.94",  # ~   12-2022
            "108.0.5359.98",  # ~   12-2022
            "108.0.5359.124",  # ~  12-2022
            "108.0.5359.179",  # ~  01-2023
            "108.0.5359.215",  # ~  01-2023
        ],
        "109": [
            "109.0.5414.74",  # ~   01-2023
            "109.0.5414.119",  # ~  01-2023
        ],
        "110": [
            "110.0.5481.77",  # ~   02-2023
            "110.0.5481.208",  # ~  03-2023
        ],
        "111": [
            "111.0.5563.110",  # ~  03-2023
            "111.0.5563.147",  # ~  03-2023
        ],
        "112": [
            "112.0.5615.49",  # ~   04-2023
            "112.0.5615.86",  # ~   04-2023
            "112.0.5615.87",  # ~   04-2023
            "112.0.5615.121",  # ~  04-2023
            "112.0.5615.137",  # ~  04-2023
            "112.0.5615.138",  # ~  04-2023
        ],
        "113": [
            "113.0.5672.126",  # ~  05-2023
        ],
        "114": [
            "114.0.5735.90",  # ~   05-2023
            "114.0.5735.133",  # ~  06-2023
            "114.0.5735.198",  # ~  06-2023
        ],
    }

    # sec-ch-ua
    __SEC_CH_UA_BASE_POS: str = "{}, {}, {}"
    __SEC_CH_UA_ITEMS: Dict[int, str] = {
        1: '"Chromium";v="{v}"',
        2: '"Google Chrome";v="{v}"',
        3: '"Not{spec_1}A{spec_2}Brand";v="{v}"',
    }
    __SEC_CH_UA_PLATFORM: List[str] = ["Linux", "Windows"]
    __SEC_CH_UA_PLATFORM_VERSION: Dict[str, List[str]] = {  # OS versions numbers
        "Linux": [
            "6.4.0",
            "6.3.0",
            "6.2.0",
            "6.1.0",
            "6.0.0",
            "5.19.0",
            "5.18.0",
            "5.17.0",
            "5.16.0",
            "5.15.0",
        ],
        "Windows": ["13.0.0", "10.0.0"],
    }
    __SEC_CH_UA_ARCH: List[str] = ["x86"]
    __SEC_CH_UA_BITNESS: List[str] = ["64", "32"]
    __SEC_CH_UA_MODEL: List[str] = ['""']
    __SEC_CH_UA_MOBILE: List[str] = [
        "?0",
        # '?1',
    ]

    # user-agent
    __USER_AGENT_STRING: str = (
        "Mozilla/5.0 ({system_information}) {platform} ({platform_details}) {extensions}"
    )
    __USER_AGENT_SYSTEM_INFORMATION: Dict[str, Dict[str, str] | Dict[str, str]] = {
        "Linux": {"64": "X11; Linux x86_64", "32": "X11; Linux x86_64"},
        "Windows": {
            "64": "Windows NT 10.0; Win64; x64",
            "32": "Windows NT 10.0",
        },
    }
    __USER_AGENT_PLATFORM: Tuple[str, str] = ("AppleWebKit", "537.36")
    __USER_AGENT_PLATFORM_DETAILS: str = "KHTML, like Gecko"
    __USER_AGENT_EXTENSIONS: str = "Chrome/{chrome_v}.0.0.0 Safari/{safari_v}"

    def __random_chrome_version(self) -> Tuple[str, str]:
        ver_num = choice(list(self.CHROME_VERSIONS.keys()))
        ver_val = choice(self.CHROME_VERSIONS.get(ver_num))

        return ver_num, ver_val

    def __build_extensions(self, item: Headers) -> str:
        return self.__USER_AGENT_EXTENSIONS.format(
            chrome_v=item.chrome_version[0],
            safari_v=self.__USER_AGENT_PLATFORM[1],
        )

    @classmethod
    def __random_pick(cls, array: List, remove: bool = True) -> str:
        item = choice(array)

        if remove:
            array.remove(item)

        return item

    @classmethod
    def __not_a_brand__random(cls) -> Tuple[str, str, str, str]:
        # 8 = './'
        # 99 = '_ ' ':-' ' :' ' ;'
        # 24 = '-.' '=?'

        spec_symbols = {
            "8": [
                "./",
            ],
            "24": [
                "-.",
                "=?",
            ],
            "99": [
                "_ ",
                ":-",
                " :",
                " ;",
                "/)",  # 115
            ],
        }

        not_a_brand_v = ["99", "24", "8"]

        v = choice(not_a_brand_v)
        v_full = f"{v}.0.0.0"
        spec_1, spec_2 = choice(spec_symbols.get(v, [0]))

        return v, v_full, spec_1, spec_2

    def __sec_ch_ua_conf__random(self) -> Dict:
        keys = list(self.__SEC_CH_UA_ITEMS.keys())

        return {
            "pos": (
                self.__random_pick(keys),
                self.__random_pick(keys),
                self.__random_pick(keys),
            ),
            "not_a_brand": self.__not_a_brand__random(),
        }

    @classmethod
    def __sec_ch_ua_full_version__random(cls, item: Headers) -> str:
        return f"{item.chrome_version[1]}"

    def __positioning(self, position: int, item: Headers) -> Tuple[str, str, str]:
        sec_ch_ua_items = deepcopy(self.__SEC_CH_UA_ITEMS)

        sec_ch_ua_items[1] = sec_ch_ua_items.get(1).format(
            v=item.chrome_version[position],
        )
        sec_ch_ua_items[2] = sec_ch_ua_items.get(2).format(
            v=item.chrome_version[position],
        )
        sec_ch_ua_items[3] = sec_ch_ua_items.get(3).format(
            v=item.sec_ch_ua_conf["not_a_brand"][position],
            spec_1=item.sec_ch_ua_conf["not_a_brand"][2],
            spec_2=item.sec_ch_ua_conf["not_a_brand"][3],
        )

        pos_1 = sec_ch_ua_items[item.sec_ch_ua_conf["pos"][0]]
        pos_2 = sec_ch_ua_items[item.sec_ch_ua_conf["pos"][1]]
        pos_3 = sec_ch_ua_items[item.sec_ch_ua_conf["pos"][2]]

        return pos_1, pos_2, pos_3

    def __sec_ch_ua__random(self, item: Headers) -> str:
        return self.__SEC_CH_UA_BASE_POS.format(*self.__positioning(0, item))

    def __sec_ch_ua_full_version_list__random(self, item: Headers) -> str:
        return self.__SEC_CH_UA_BASE_POS.format(*self.__positioning(1, item))

    def __sec_ch_ua_platform__random(self) -> str:
        return choice(self.__SEC_CH_UA_PLATFORM)

    def __sec_ch_ua_platform_version__random(self, item: Headers) -> str:
        return choice(self.__SEC_CH_UA_PLATFORM_VERSION[item.sec_ch_ua_platform])

    def __sec_ch_ua_arch__random(self) -> str:
        return choice(self.__SEC_CH_UA_ARCH)

    def __sec_ch_ua_bitness_random(self) -> str:
        return choice(self.__SEC_CH_UA_BITNESS)

    def __sec_ch_ua_model_random(self) -> str:
        return choice(self.__SEC_CH_UA_MODEL)

    def __sec_ch_ua_mobile__random(self) -> str:
        return choice(self.__SEC_CH_UA_MOBILE)

    def __user_agent__random(self, item: Headers) -> str:
        platform = f"{self.__USER_AGENT_PLATFORM[0]}/{self.__USER_AGENT_PLATFORM[1]}"

        extensions = self.__build_extensions(item)
        system_information = self.__USER_AGENT_SYSTEM_INFORMATION[
            item.sec_ch_ua_platform
        ][item.sec_ch_ua_bitness]

        return self.__USER_AGENT_STRING.format(
            system_information=system_information,
            platform=platform,
            platform_details=self.__USER_AGENT_PLATFORM_DETAILS,
            extensions=extensions,
        )

    @classmethod
    def add__sec_ch_ua(cls, item: Headers) -> None:
        """
        Set sec-ch-ua headers:
            - sec-ch-ua
            - sec-ch-ua-full-version
            - sec-ch-ua-full-version-list
            - sec-ch-ua-platform
            - sec-ch-ua-arch
            - sec-ch-ua-bitness
            - sec-ch-ua-mobile
            - sec-ch-ua-model
        """
        item.options["sec-ch-ua"] = item.sec_ch_ua
        item.options["sec-ch-ua-full-version"] = item.sec_ch_ua_full_version
        item.options["sec-ch-ua-full-version-list"] = item.sec_ch_ua_full_version_list
        item.options["sec-ch-ua-platform"] = item.sec_ch_ua_platform
        item.options["sec-ch-ua-platform-version"] = item.sec_ch_ua_full_version_list
        item.options["sec-ch-ua-arch"] = item.sec_ch_ua_arch
        item.options["sec-ch-ua-bitness"] = item.sec_ch_ua_bitness
        item.options["sec-ch-ua-mobile"] = item.sec_ch_ua_mobile
        item.options["sec-ch-ua-model"] = item.sec_ch_ua_model

    @classmethod
    def add__user_agent(cls, item: Headers) -> None:
        """
        Set user-agent header
        """
        item.options["user-agent"] = item.user_agent

    def randomize_headers(self, headers: Headers) -> Dict[str, str]:
        return self.__randomize(headers).headers

    def __randomize(self, item: Headers) -> Headers:
        # Chrome version
        item.chrome_version = self.__random_chrome_version()

        # sec-ch-ua
        item.sec_ch_ua_conf = self.__sec_ch_ua_conf__random()

        item.sec_ch_ua = self.__sec_ch_ua__random(item)
        item.sec_ch_ua_full_version = self.__sec_ch_ua_full_version__random(item)
        item.sec_ch_ua_full_version_list = self.__sec_ch_ua_full_version_list__random(
            item,
        )
        item.sec_ch_ua_platform = self.__sec_ch_ua_platform__random()
        item.sec_ch_ua_platform_version = self.__sec_ch_ua_platform_version__random(item)
        item.sec_ch_ua_mobile = self.__sec_ch_ua_mobile__random()
        item.sec_ch_ua_arch = self.__sec_ch_ua_arch__random()
        item.sec_ch_ua_bitness = self.__sec_ch_ua_bitness_random()
        item.sec_ch_ua_model = self.__sec_ch_ua_model_random()

        self.add__sec_ch_ua(item)

        # user-agent
        item.user_agent = self.__user_agent__random(item)

        self.add__user_agent(item)

        return item
