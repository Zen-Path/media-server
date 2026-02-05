import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from common.helpers import run_command
from common.logger import logger


@dataclass
class DownloadReportItem:
    url: str
    status: bool = True
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    log: str = ""
    output: str = ""
    files: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# These patterns represent single-item URLs that gallery-dl would
# otherwise parse but we KNOW aren't collections we want to recurse.
NON_COLLECTION_PATTERNS = [
    re.compile(r"^https?://(?:www\.)?x\.com/\w+/status/\d+"),
    re.compile(r"^https?://(?:www\.)?pornpics\.com/galleries/[\w-]+/?"),
    re.compile(r"^https?://(?:www\.)?xnxx\.com/video-.*"),
    re.compile(r"^https?://(?:www\.)?reddit\.com/r/\w+/comments/.*/?"),
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


@dataclass
class OperationResult:
    status: bool
    data: Any  # Usually the ID (int)
    error: Optional[str] = None

    def get_overall_status(self) -> bool:
        """
        Returns True if the operation was successful.
        If data is a list of OperationResults, returns True if ANY are successful.
        """
        if not isinstance(self.data, list):
            return self.status

        for result in self.data:
            # Recursively check if any child result succeeded
            if isinstance(result, OperationResult):
                if result.status:
                    return True

        return False

    def to_dict(self):
        data_serialized = self.data
        if isinstance(self.data, list):
            data_serialized = [
                asdict(r) if isinstance(r, OperationResult) else r for r in self.data
            ]

        return {
            "status": self.get_overall_status(),
            "error": self.error,
            "data": data_serialized,
        }
