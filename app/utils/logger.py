import logging
import sys

from colorama import Fore, Style, init

logger = logging.getLogger(__name__)


# Initialize colorama
init(autoreset=True)

LOG_COLORS = {
    logging.DEBUG: Fore.BLUE,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
}


LEVEL_NAME_MAP = {
    logging.DEBUG: "DBG",
    logging.INFO: "INF",
    logging.WARNING: "WRN",
    logging.ERROR: "ERR",
    logging.CRITICAL: "CRT",
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Patch the levelname
        if record.levelno in LEVEL_NAME_MAP:
            record.levelname = LEVEL_NAME_MAP[record.levelno]

        color = LOG_COLORS.get(record.levelno, "")
        formatted = super().format(record)
        return f"{color}{formatted}{Style.RESET_ALL}"


def setup_logging(
    logger: logging.Logger,
    level: int = logging.ERROR,
    date_fmt: str = "%H:%M:%S",
) -> None:
    """
    Configure a specific logger with a colorized stream handler.
    To display the full timestamp, use date_fmt="%Y-%m-%d %H:%M:%S"
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = ColoredFormatter(
        fmt="%(levelname).3s | %(asctime)s | %(message)s", datefmt=date_fmt
    )
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.handlers.clear()  # Remove existing handlers to avoid duplicates
    logger.propagate = False  # Prevent bubbling to ancestor loggers
    logger.addHandler(handler)
