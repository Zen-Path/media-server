from enum import IntEnum


# fmt: off
class DownloadStatus(IntEnum):
    PENDING     = 0
    IN_PROGRESS = 1
    DONE        = 2
    FAILED      = 3
    MIXED       = 4
# fmt: on


# fmt: off
class MediaType(IntEnum):
    GALLERY     = 0
    IMAGE       = 1
    VIDEO       = 2
    AUDIO       = 3
    TEXT        = 4
# fmt: on


# fmt: off
class EventType(IntEnum):
    CREATE      = 0
    UPDATE      = 1
    DELETE      = 2
    PROGRESS    = 3
# fmt: on


class ScraperConfig:
    TIMEOUT = 10
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


MAX_TITLE_LENGTH = 255
