import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from app.constants import DownloadStatus, MediaType
from app.services import download_service
from app.services.download_service import initialize_download
from app.utils.gallery_dl import download_gallery
from app.utils.scraper import expand_collection_urls
from app.utils.tools import DownloadReportItem


def process_download_request(
    urls: List[str],
    media_type: Optional[MediaType],
    range_start: Optional[int],
    range_end: Optional[int],
) -> Dict[str, Any]:
    """
    Orchestrates the download process.
    """

    report: Dict[str, DownloadReportItem] = {}

    # INITIAL RECORDING

    # We store the initial batch to ensure we have a "paper trail"
    initial_queue = []
    for url in list(set(urls)):
        m_type_val = media_type.value if media_type else None

        success, download_id, error = download_service.initialize_download(
            url, m_type_val
        )
        report[url] = DownloadReportItem(url=url, status=success, error=error)

        if success:
            initial_queue.append((download_id, url))

    # EXPANSION
    final_processing_queue = []
    seen_urls = set()

    if not media_type or media_type == MediaType.GALLERY:
        for parent_id, parent_url in initial_queue:
            seen_urls.add(parent_url)
            expanded_urls = expand_collection_urls(parent_url)

            if not expanded_urls:
                final_processing_queue.append((parent_id, parent_url))
                continue

            report[parent_url].log += f" Expanded into {len(expanded_urls)} items."

            for child_url in expanded_urls:
                if child_url in seen_urls:
                    continue

                child_success, child_id, child_error = initialize_download(
                    child_url, media_type
                )

                # Regardless of success status, we want to keep track of the url,
                # since if it fails and multiple parents expand into lists containing
                # this url, we would keep re-trying to add it to the db. Retries should
                # be a user initiated action.
                seen_urls.add(child_url)

                report[child_url] = DownloadReportItem(
                    url=child_url,
                    status=child_success,
                    error=child_error,
                    log=f"Child of #{parent_id}",
                )

                if child_success:
                    final_processing_queue.append((child_id, child_url))
    else:
        # Non-gallery types will never expand
        final_processing_queue = initial_queue

    # PROCESSING
    for i, (download_id, url) in enumerate(final_processing_queue):
        title = _scrape_title(url, report)

        _execute_download(url, media_type, range_start, range_end, report)

        final_status = (
            DownloadStatus.DONE if report[url].status else DownloadStatus.FAILED
        )
        success, error = download_service.finalize_download(
            download_id, title, final_status.value
        )

        if report[url].status:
            report[url].status = success
        if error:
            report[url].error = error

    return {url: item.to_dict() for url, item in report.items()}


def _scrape_title(url: str, report: Dict[str, DownloadReportItem]) -> Optional[str]:
    """Helper to scrape title using Requests + BS4."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            if soup.title and soup.title.string:
                return soup.title.string.strip()
        else:
            report[url].warnings.append(f"Title scrape HTTP {response.status_code}")

    except Exception as e:
        report[url].warnings.append(f"Title scrape failed: {str(e)}")

    return None


def _execute_download(url: str, media_type: Optional[MediaType], start, end, report):
    """Helper to run the download command and parse output."""
    try:
        if media_type == MediaType.GALLERY or media_type is None:
            cmd_result = download_gallery([url], start, end)

            report[url].output = cmd_result.output
            report[url].status = cmd_result.return_code == 0

            # Parse Output for errors
            _parse_gallery_output(url, report)
    except Exception as e:
        report[url].status = False
        report[url].error = str(e)


def _parse_gallery_output(url, report):
    """Regex parsing of gallery-dl output."""
    no_results = r"^\[[^\]]+\]\[info\] No results for"
    too_large = r"^\[[^\]]+\]\[warning\] File size larger"
    catchall = r"^\[[^\]]+\]\[error\]"

    if not report[url].status and not report[url].error:
        report[url].error = "[gallery-dl] Unknown failure"

    lines = report[url].output.splitlines()
    for line in lines:
        if re.search(no_results, line):
            report[url].status = False
            report[url].error = "No results found."
        elif re.search(too_large, line):
            report[url].status = False
            report[url].error = "File too large."
        elif re.search(catchall, line):
            report[url].status = False
            report[url].error = line

        if line.startswith("./"):
            report[url].files.append(line)
