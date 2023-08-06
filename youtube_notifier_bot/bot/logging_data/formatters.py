from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING, Formatter


class ColourFormatter(Formatter):
    NORMAL = 10
    BOLD = 1
    FADED = 2

    GREY = 37
    # WHITE = 38
    GREEN = 32
    YELLOW = 33
    RED = 31

    CSI = "\x1b[{};{}m"
    RESET = "\x1b[0m"

    def __init__(self, fmt: str, datefmt: str):
        super().__init__(fmt=fmt, datefmt=datefmt)

        self.FORMATS = {
            NOTSET: self.CSI.format(self.FADED, self.GREY) + self._fmt + self.RESET,
            DEBUG: self.CSI.format(self.NORMAL, self.GREY) + self._fmt + self.RESET,
            INFO: self.CSI.format(self.NORMAL, self.GREEN) + self._fmt + self.RESET,
            WARNING: self.CSI.format(self.NORMAL, self.YELLOW) + self._fmt + self.RESET,
            ERROR: self.CSI.format(self.NORMAL, self.RED) + self._fmt + self.RESET,
            CRITICAL: self.CSI.format(self.BOLD, self.RED) + self._fmt + self.RESET,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(fmt=log_fmt, datefmt=self.datefmt)
        return formatter.format(record)
