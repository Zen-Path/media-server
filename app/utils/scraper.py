import json
import re
from pathlib import Path
from typing import List

from common.helpers import run_command
from common.logger import logger

# These patterns represent single-item URLs that gallery-dl would
# otherwise parse but we KNOW aren't collections we want to recurse.
NON_COLLECTION_PATTERNS = [
    re.compile(r"^https?://(?:www\.)?x\.com/\w+/status/\d+"),
    re.compile(r"^https?://(?:www\.)?pornpics\.com/galleries/[\w-]+/?"),
    re.compile(r"^https?://(?:www\.)?xnxx\.com/video-.*"),
    re.compile(r"^https?://(?:www\.)?reddit\.com/r/\w+/comments/.*/?"),
    re.compile(r"^(?:https?://)?(?:www\.)?example\.com.*"),
]

# Common direct media extensions
MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".mp4",
    ".mkv",
    ".mov",
    ".mp3",
    ".zip",
}


def is_direct_file(url: str) -> bool:
    """Check if the URL points directly to a file extension."""
    path = Path(url.split("?")[0])  # Strip query params
    return path.suffix.lower() in MEDIA_EXTENSIONS


def is_known_single_item(url: str) -> bool:
    """Check if the URL matches a known pattern that doesn't need expansion."""
    return any(pattern.search(url) for pattern in NON_COLLECTION_PATTERNS)


def expand_collection_urls(url: str, depth: int = 0) -> List[str]:
    """
    Determines if a URL is a collection and expands it.
    Rejects direct file urls and known patterns.
    """

    if depth > 3:
        return []

    if is_direct_file(url):
        logger.debug(f"Fast-path: skipping expansion for direct file: {url}")
        return []

    if is_known_single_item(url):
        logger.debug(f"Fast-path: skipping expansion for known single-item: {url}")
        return []

    try:
        cmd = ["gallery-dl", "-s", "-j", url]
        result = run_command(cmd)
        if not result.success:
            return []

        data = json.loads(result.output)

        # If there is only ONE unique level (e.g., all are level 6), it is probably
        # a collection of gallery links.
        # TODO: investigate gallery returns type to improve this logic
        levels = [entry[0] for entry in data if entry[0] > 1]
        unique_levels = set(levels)
        if len(unique_levels) != 1:
            return []

        child_urls = []
        for entry in data:
            # Entry structure: [level, content]
            if (
                len(entry) >= 2
                and isinstance(entry[1], str)
                and entry[1].startswith("http")
            ):
                c_url = entry[1]
                if c_url != url:  # Prevent self-reference loops
                    child_urls.append(c_url)
                    child_urls.extend(expand_collection_urls(c_url, depth + 1))

        return list(dict.fromkeys(child_urls))

    except Exception as e:
        logger.warning(f"Expansion error for {url}: {e}")
        return []
