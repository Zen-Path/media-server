import re
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from common.logger import logger
from flask import current_app, jsonify, request
from scripts.media_server.routes.api import bp
from scripts.media_server.src.constants import (
    DownloadStatus,
    EventType,
    MediaType,
    ScraperConfig,
)
from scripts.media_server.src.extensions import db
from scripts.media_server.src.models import Download
from scripts.media_server.src.utils.downloaders import Gallery
from scripts.media_server.src.utils.scraper import expand_collection_urls
from scripts.media_server.src.utils.tools import DownloadReportItem


def start_download_record(
    url: str, media_type: Optional[int]
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Initializes a download entry in the database and notifies the dashboard.

    This function creates a 'shell' record, allowing the system to track that
    a download is active before the heavy processing begins.

    Returns:
        A tuple of (success_status, generated_id, error_message).
    """
    try:
        new_download = Download(url=url, media_type=media_type)

        db.session.add(new_download)
        db.session.commit()

        last_id = new_download.id

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.CREATE,
                {
                    "id": last_id,
                    "url": url,
                    "mediaType": media_type,
                    "startTime": new_download.start_time_iso,
                    "status": new_download.status,
                    "statusMessage": new_download.status_msg,
                },
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, last_id, None

    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to initialize download record: {e}"
        logger.error(err_msg)
        return False, None, err_msg


def complete_download_record(
    download_id: int, title: Optional[str], status: DownloadStatus
) -> Tuple[bool, Optional[str]]:
    """
    Finalizes an existing download record with its metadata and notifies the dashboard.

    Updates the specific row with the final title and the timestamp of
    completion.

    Returns:
        A tuple of (success_status, error_message).
    """
    try:
        record = db.session.get(Download, download_id)
        if not record:
            return False, f"Download ID {download_id} not found."

        record.title = title
        record.end_time = datetime.now(timezone.utc)
        record.status = status

        db.session.commit()

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.UPDATE,
                {
                    "id": download_id,
                    "title": title,
                    "endTime": record.end_time_iso,
                    "updatedTime": record.updated_time_iso,
                    "orderNumber": record.order_number,
                    "status": record.status,
                    "statusMessage": record.status_msg,
                },
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, None
    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to update download record #{download_id}: {e}"
        logger.error(err_msg)
        return False, err_msg


@bp.route("/media/download", methods=["POST"])
def download_media():
    data = request.get_json()
    urls = data.get("urls")
    media_type = data.get("mediaType")
    range_start = data.get("rangeStart")
    range_end = data.get("rangeEnd")

    # Validation

    ## URLs
    if (
        not urls
        or not isinstance(urls, list)
        or not all(isinstance(url, str) for url in urls)
    ):
        return jsonify({"error": "'urls' must be a list of strings."}), 400

    ## Media Type
    if media_type is not None:
        if not isinstance(media_type, int):
            return jsonify({"error": "'mediaType' must be an int."}), 400
        try:
            media_type = MediaType(media_type)
        except ValueError:
            return jsonify({"error": f"Invalid mediaType value: {media_type}"}), 400

    ## Range Parts
    if range_start and not isinstance(range_start, int):
        return jsonify({"error": "'rangeStart' must be an int."}), 400

    if range_end and not isinstance(range_end, int):
        return jsonify({"error": "'rangeEnd' must be an int."}), 400

    report: Dict[str, DownloadReportItem] = {}

    # INITIAL RECORDING

    # We store the initial batch to ensure we have a "paper trail"
    initial_queue = []
    for url in list(set(urls)):
        success, download_id, error = start_download_record(url, media_type)
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

                child_success, child_id, child_error = start_download_record(
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

    # gallery-dl output patterns
    no_results_pattern = r"^\[[^\]]+\]\[info\] No results for"
    larger_than_allowed_pattern = r"^\[[^\]]+\]\[warning\] File size larger"
    catchall_error_pattern = r"^\[[^\]]+\]\[error\]"

    final_processing_count = len(final_processing_queue)
    for i, (download_id, url) in enumerate(final_processing_queue):
        # Scrape title
        title = None

        try:
            headers = {"User-Agent": ScraperConfig.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=ScraperConfig.TIMEOUT)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
            else:
                report[url].warnings.append(f"Title scrape HTTP {response.status_code}")

        except Exception as e:
            report[url].warnings.append(f"Title scrape failed: {str(e)}")

        # Download
        try:
            match media_type:
                case MediaType.GALLERY | None:
                    cmd_result = Gallery.download([url], range_start, range_end)
                    report[url].output = cmd_result.output
                    report[url].status = cmd_result.return_code == 0

                    if not report[url].status:
                        report[
                            url
                        ].error = (
                            f"[gallery-dl] Command failed: {cmd_result.return_code}"
                        )
                    else:
                        for line in report[url].output.splitlines():
                            if re.search(no_results_pattern, line):
                                report[url].status = False
                                report[
                                    url
                                ].error = "[gallery-dl] No results found for url."
                            elif re.search(larger_than_allowed_pattern, line):
                                report[url].status = False
                                report[
                                    url
                                ].error = "[gallery-dl] File size larger than allowed."
                            elif re.search(catchall_error_pattern, line):
                                report[url].status = False
                                report[url].error = f"[gallery-dl] {line}."

                    if report[url].status:
                        for line in report[url].output.splitlines():
                            if line.startswith("./"):
                                report[url].files.append(line)

        except Exception as e:
            report[url].status = False
            report[url].error = str(e)

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.PROGRESS,
                {"id": download_id, "current": i, "total": final_processing_count},
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        # Finalize DB record
        success, error = complete_download_record(
            download_id,  # type: ignore[arg-type]
            title,
            DownloadStatus.DONE if report[url].status else DownloadStatus.FAILED,
        )

        if report[url].status:
            report[url].status = success
        if error:
            report[url].error = error

    final_json_report = {url: item.to_dict() for url, item in report.items()}
    return jsonify(final_json_report), 200
