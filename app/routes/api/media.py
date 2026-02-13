from typing import Dict

from flask import current_app, request
from marshmallow import ValidationError

from app.constants import DownloadStatus, EventType, MediaType
from app.routes.api import bp
from app.schemas.execution import DownloadRequestSchema
from app.services.download_service import (
    finalize_download,
    initialize_download,
)
from app.utils.api_response import api_response
from app.utils.downloaders import Gallery
from app.utils.logger import logger
from app.utils.scraper import expand_collection_urls, scrape_title
from app.utils.tools import DownloadReportItem


@bp.route("/media/download", methods=["POST"])
def download_media():
    json_data = request.get_json(silent=True)
    if not json_data:
        return api_response(error="Missing JSON payload", status_code=400)

    try:
        data = DownloadRequestSchema().load(json_data)
        items = data["items"]
        range_start = data.get("range_start")
        range_end = data.get("range_end")

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    report: Dict[str, DownloadReportItem] = {}

    # DEDUPLICATION

    # First URL seen wins. Any subsequent duplicates are ignored.
    unique_items = {}
    for item in items:
        url = item["url"]
        if url not in unique_items:
            unique_items[url] = item

    # INITIAL RECORDING

    # We store the initial batch to ensure we have a "paper trail"
    initial_queue = []
    for url, item_data in unique_items.items():
        item_media_type = item_data.get("media_type")
        provided_title = item_data.get("title")

        success, error, record_dict = initialize_download(url, item_media_type)
        download_id = record_dict["id"] if success and record_dict else None
        report[url] = DownloadReportItem(url=url, status=success, error=error)

        if success:
            initial_queue.append((download_id, url, item_media_type, provided_title))

    # EXPANSION

    final_processing_queue = []
    seen_urls = set(unique_items.keys())

    for parent_id, parent_url, item_media_type, item_title in initial_queue:
        if item_media_type and item_media_type != MediaType.GALLERY:
            # Non-gallery types will never expand
            final_processing_queue.append(
                (parent_id, parent_url, item_media_type, item_title)
            )
            continue

        expanded_urls = expand_collection_urls(parent_url)

        if not expanded_urls:
            final_processing_queue.append(
                (parent_id, parent_url, item_media_type, item_title)
            )
            continue

        report[parent_url].log += f" Expanded into {len(expanded_urls)} items."

        for child_url in expanded_urls:
            if child_url in seen_urls:
                continue

            child_success, child_error, child_record = initialize_download(
                child_url, item_media_type
            )
            child_id = child_record["id"] if child_success and child_record else None

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
                final_processing_queue.append(
                    (child_id, child_url, item_media_type, None)
                )

    # PROCESSING

    finalized_records = []

    for download_id, url, item_media_type, provided_title in final_processing_queue:
        if download_id is None:
            continue

        title = provided_title if provided_title else scrape_title(url)

        # Download
        try:
            match item_media_type:
                case MediaType.GALLERY | None:
                    report_result = Gallery.download([url], range_start, range_end)
                    report[url].output = report_result.output
                    report[url].status = report_result.status
                    report[url].error = report_result.error
                    report[url].files = report_result.files

        except Exception as e:
            logger.exception(e)

            report[url].status = False
            report[url].error = str(e)

        # Finalize DB record
        success, error, record_dict = finalize_download(
            download_id,  # type: ignore[arg-type]
            title,
            DownloadStatus.DONE if report[url].status else DownloadStatus.FAILED,
        )

        if report[url].status:
            report[url].status = success

        if error:
            report[url].error = error

        if record_dict:
            finalized_records.append(record_dict)

    # BULK ANNOUNCEMENT

    if finalized_records:
        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.UPDATE, finalized_records
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

    final_json_report = [item.to_dict() for item in report.values()]
    return api_response(data=final_json_report)
