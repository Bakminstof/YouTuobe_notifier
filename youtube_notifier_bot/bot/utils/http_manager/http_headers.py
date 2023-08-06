from copy import deepcopy
from random import choice
from typing import Dict, List, Tuple


class ChromeHeadersBuilder:
    CHROME_VERSIONS = {
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
            "107.0.5304.121",  # ~   11-2022
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
    __SEC_CH_UA_BASE_POS = "{}, {}, {}"
    __SEC_CH_UA_ITEMS = {
        1: '"Chromium";v="{v}"',
        2: '"Google Chrome";v="{v}"',
        3: '"Not{spec_1}A{spec_2}Brand";v="{v}"',
    }
    __SEC_CH_UA_PLATFORM = ["Linux", "Windows"]
    __SEC_CH_UA_PLATFORM_VERSION = {  # OS versions numbers
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
    __SEC_CH_UA_ARCH = ["x86"]
    __SEC_CH_UA_BITNESS = ["64", "32"]
    __SEC_CH_UA_MODEL = ['""']
    __SEC_CH_UA_MOBILE = [
        "?0",
        # '?1',
    ]

    # user-agent
    __USER_AGENT_STRING = (
        "Mozilla/5.0 ({system_information}) {platform} ({platform_details}) {extensions}"
    )
    __USER_AGENT_SYSTEM_INFORMATION = {
        "Linux": {"64": "X11; Linux x86_64", "32": "X11; Linux x86_64"},
        "Windows": {
            "64": "Windows NT 10.0; Win64; x64",
            "32": "Windows NT 10.0",
        },
    }
    __USER_AGENT_PLATFORM = ("AppleWebKit", "537.36")
    __USER_AGENT_PLATFORM_DETAILS = "KHTML, like Gecko"
    __USER_AGENT_EXTENSIONS = "Chrome/{chrome_v}.0.0.0 Safari/{safari_v}"

    @classmethod
    def __random_chrome_version(cls) -> Tuple[str, str]:
        ver_num = choice(list(cls.CHROME_VERSIONS.keys()))
        ver_val = choice(cls.CHROME_VERSIONS.get(ver_num))

        return ver_num, ver_val

    def __build_extensions(self) -> str:
        return self.__USER_AGENT_EXTENSIONS.format(
            chrome_v=self.chrome_version[0], safari_v=self.__USER_AGENT_PLATFORM[1]
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
            ],
        }

        not_a_brand_v = ["99", "24", "8"]

        v = choice(not_a_brand_v)
        v_full = "{v}.0.0.0".format(v=v)
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

    def __sec_ch_ua_full_version__random(self) -> str:
        return "{v}".format(v=self.chrome_version[1])

    def __positioning(self, position: int) -> Tuple[str, str, str]:
        items = deepcopy(self.__SEC_CH_UA_ITEMS)

        items[1] = items.get(1).format(v=self.chrome_version[position])
        items[2] = items.get(2).format(v=self.chrome_version[position])
        items[3] = items.get(3).format(
            v=self.__sec_ch_ua_conf["not_a_brand"][position],
            spec_1=self.__sec_ch_ua_conf["not_a_brand"][2],
            spec_2=self.__sec_ch_ua_conf["not_a_brand"][3],
        )

        pos_1 = items[self.__sec_ch_ua_conf["pos"][0]]
        pos_2 = items[self.__sec_ch_ua_conf["pos"][1]]
        pos_3 = items[self.__sec_ch_ua_conf["pos"][2]]

        return pos_1, pos_2, pos_3

    def __sec_ch_ua__random(self) -> str:
        return self.__SEC_CH_UA_BASE_POS.format(*self.__positioning(0))

    def __sec_ch_ua_full_version_list__random(self) -> str:
        return self.__SEC_CH_UA_BASE_POS.format(*self.__positioning(1))

    def __sec_ch_ua_platform__random(self) -> str:
        return choice(self.__SEC_CH_UA_PLATFORM)

    def __sec_ch_ua_platform_version__random(self) -> str:
        return choice(self.__SEC_CH_UA_PLATFORM_VERSION[self.sec_ch_ua_platform])

    def __sec_ch_ua_arch__random(self) -> str:
        return choice(self.__SEC_CH_UA_ARCH)

    def __sec_ch_ua_bitness_random(self) -> str:
        return choice(self.__SEC_CH_UA_BITNESS)

    def __sec_ch_ua_model_random(self) -> str:
        return choice(self.__SEC_CH_UA_MODEL)

    def __sec_ch_ua_mobile__random(self) -> str:
        return choice(self.__SEC_CH_UA_MOBILE)

    def __user_agent__random(self) -> str:
        platform = "{p}/{v}".format(
            p=self.__USER_AGENT_PLATFORM[0], v=self.__USER_AGENT_PLATFORM[1]
        )
        extensions = self.__build_extensions()
        system_information = self.__USER_AGENT_SYSTEM_INFORMATION[
            self.sec_ch_ua_platform
        ][self.sec_ch_ua_bitness]

        return self.__USER_AGENT_STRING.format(
            system_information=system_information,
            platform=platform,
            platform_details=self.__USER_AGENT_PLATFORM_DETAILS,
            extensions=extensions,
        )

    def build_sec_ch_ua(self) -> None:
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
        self.headers["sec-ch-ua"] = self.sec_ch_ua
        self.headers["sec-ch-ua-full-version"] = self.sec_ch_ua_full_version
        self.headers["sec-ch-ua-full-version-list"] = self.sec_ch_ua_full_version_list
        self.headers["sec-ch-ua-platform"] = self.sec_ch_ua_platform
        self.headers["sec-ch-ua-platform-version"] = self.sec_ch_ua_full_version_list
        self.headers["sec-ch-ua-arch"] = self.sec_ch_ua_arch
        self.headers["sec-ch-ua-bitness"] = self.sec_ch_ua_bitness
        self.headers["sec-ch-ua-mobile"] = self.sec_ch_ua_mobile
        self.headers["sec-ch-ua-model"] = self.sec_ch_ua_model

    def build_user_agent(self) -> None:
        """
        Set user-agent header
        """
        self.headers["user-agent"] = self.user_agent

    def __init__(self, random: bool = True):
        self.chrome_version: Tuple[str, str] | None = None

        self.headers = {}

        # sec-ch-ua
        self.__sec_ch_ua_conf: Dict | None = None

        self.sec_ch_ua: str | None = None
        self.sec_ch_ua_full_version: str | None = None
        self.sec_ch_ua_full_version_list: str | None = None
        self.sec_ch_ua_platform: str | None = None
        self.sec_ch_ua_platform_version: str | None = None
        self.sec_ch_ua_arch: str | None = None
        self.sec_ch_ua_bitness: str | None = None
        self.sec_ch_ua_mobile: str | None = None
        self.sec_ch_ua_model: str | None = None

        self.user_agent: str | None = None

        if random:
            self.__randomize()

    def __randomize(self) -> None:
        # Chrome version
        self.chrome_version = self.__random_chrome_version()

        # sec-ch-ua
        self.__sec_ch_ua_conf = self.__sec_ch_ua_conf__random()

        self.sec_ch_ua = self.__sec_ch_ua__random()
        self.sec_ch_ua_full_version = self.__sec_ch_ua_full_version__random()
        self.sec_ch_ua_full_version_list = self.__sec_ch_ua_full_version_list__random()
        self.sec_ch_ua_platform = self.__sec_ch_ua_platform__random()
        self.sec_ch_ua_platform_version = self.__sec_ch_ua_platform_version__random()
        self.sec_ch_ua_mobile = self.__sec_ch_ua_mobile__random()
        self.sec_ch_ua_arch = self.__sec_ch_ua_arch__random()
        self.sec_ch_ua_bitness = self.__sec_ch_ua_bitness_random()
        self.sec_ch_ua_model = self.__sec_ch_ua_model_random()

        self.build_sec_ch_ua()

        # user-agent
        self.user_agent = self.__user_agent__random()

        self.build_user_agent()
