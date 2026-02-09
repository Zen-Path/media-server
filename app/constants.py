import re
from enum import IntEnum


# fmt: off
class DownloadStatus(IntEnum):
    PENDING     = 1
    IN_PROGRESS = 2
    DONE        = 3
    FAILED      = 4
    MIXED       = 5
# fmt: on


# fmt: off
class MediaType(IntEnum):
    GALLERY     = 1
    IMAGE       = 2
    VIDEO       = 3
    AUDIO       = 4
    TEXT        = 5
# fmt: on


# fmt: off
class EventType(IntEnum):
    CREATE      = 1
    UPDATE      = 2
    DELETE      = 3
    PROGRESS    = 4
# fmt: on


class ScraperConfig:
    TIMEOUT = 10
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    MAX_BYTES_TO_READ = 20 * 1024  # Search for a title within this range


MAX_TITLE_LENGTH = 255


# Common direct media extensions
# fmt: off
MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".mp3", ".wav", ".flac", ".ogg",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".pdf"
}
# fmt: on

# These patterns represent single-item URLs that gallery-dl would
# otherwise parse but we KNOW aren't collections we want to recurse.
NON_COLLECTION_PATTERNS = [
    re.compile(r"^https?://(?:www\.)?x\.com/\w+/status/\d+"),
    re.compile(r"^https?://(?:www\.)?pornpics\.com/galleries/[\w-]+/?"),
    re.compile(r"^https?://(?:www\.)?xnxx\.com/video-.*"),
    re.compile(r"^https?://(?:www\.)?reddit\.com/r/\w+/comments/.*/?"),
    re.compile(r"^(?:https?://)?(?:www\.)?example\.com.*"),
]
