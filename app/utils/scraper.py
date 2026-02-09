import html
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import unquote, urlparse

import requests

from app.constants import (
    MEDIA_EXTENSIONS,
    NON_COLLECTION_PATTERNS,
    ScraperConfig,
)
from app.utils.logger import logger
from app.utils.tools import run_command


def is_direct_file(url: str) -> bool:
    """Check if the URL points directly to a file extension."""
    path = Path(urlparse(url).path)
    return path.suffix.lower() in MEDIA_EXTENSIONS


def is_known_single_item(url: str) -> bool:
    """Check if the URL matches a known pattern that doesn't need expansion."""
    return any(pattern.search(url) for pattern in NON_COLLECTION_PATTERNS)


def get_filename_from_url(url: str) -> str:
    """
    Extracts a clean filename from a URL.
    Example: http://site.com/cool-image.jpg?foo=bar -> "cool-image.jpg - site.com"
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = Path(path).name  # Keep extension in the name for clarity
    domain = parsed.netloc

    if not filename:
        filename = "file"

    return f"{filename} - {domain}"


def scrape_title(url: str, headers: Optional[Dict] = None) -> str:
    """
    Scrapes the title of a webpage OR generates a filename for direct files.
    """
    request_headers = headers or {"User-Agent": ScraperConfig.USER_AGENT}

    if is_direct_file(url):
        return get_filename_from_url(url)

    try:
        with requests.Session() as session:
            head_resp = session.head(
                url,
                headers=request_headers,
                timeout=ScraperConfig.TIMEOUT,
                allow_redirects=True,
            )
            head_resp.raise_for_status()

            content_type = head_resp.headers.get("Content-Type", "").lower()

            # If explicit non-html type, abort scraping, except for generic octet-stream
            if (
                not content_type
                or "text/html" not in content_type
                and "application/xhtml" not in content_type
            ):
                if "octet-stream" not in content_type:
                    return get_filename_from_url(url)

            response = session.get(
                url, headers=request_headers, timeout=ScraperConfig.TIMEOUT, stream=True
            )
            response.raise_for_status()

            content_accumulated = b""

            # Read chunks until we find the title or hit the byte limit
            for chunk in response.iter_content(chunk_size=1024):
                content_accumulated += chunk

                text_chunk = content_accumulated.decode("utf-8", errors="ignore")

                # re.DOTALL allows matching across newlines
                match = re.search(
                    r"<title>(.*?)</title>", text_chunk, re.IGNORECASE | re.DOTALL
                )

                if match:
                    raw_title = match.group(1).strip()
                    return html.unescape(raw_title)

                if len(content_accumulated) > ScraperConfig.MAX_BYTES_TO_READ:
                    break

            return get_filename_from_url(url)

    except Exception:
        return get_filename_from_url(url)


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
