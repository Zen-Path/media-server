from typing import Dict

from flask import request
from marshmallow import ValidationError

from app.constants import (
    DownloadStatus,
    MediaType,
)
from app.routes.api import bp
from app.schemas.execution import DownloadRequestSchema
from app.services.download_service import (
    finalize_download,
    initialize_download,
)
from app.utils.api_response import api_response
from app.utils.downloaders import Gallery
from app.utils.scraper import expand_collection_urls, scrape_title
from app.utils.tools import DownloadReportItem


@bp.route("/media/download", methods=["POST"])
def download_media():
    json_data = request.get_json()

    try:
        data = DownloadRequestSchema().load(json_data)
        urls = data["urls"]
        media_type = data.get("media_type")
        range_start = data.get("range_start")
        range_end = data.get("range_end")

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    report: Dict[str, DownloadReportItem] = {}

    # INITIAL RECORDING

    # We store the initial batch to ensure we have a "paper trail"
    initial_queue = []
    for url in list(set(urls)):
        success, download_id, error = initialize_download(url, media_type)
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

    for download_id, url in final_processing_queue:
        title = scrape_title(url)

        # Download
        try:
            match media_type:
                case MediaType.GALLERY | None:
                    report_result = Gallery.download([url], range_start, range_end)
                    report[url].output = report_result.output
                    report[url].status = report_result.status
                    report[url].error = report_result.error
                    report[url].files = report_result.files

        except Exception as e:
            report[url].status = False
            report[url].error = str(e)

        # Finalize DB record
        success, error = finalize_download(
            download_id,  # type: ignore[arg-type]
            title,
            DownloadStatus.DONE if report[url].status else DownloadStatus.FAILED,
        )

        if report[url].status:
            report[url].status = success
        if error:
            report[url].error = error

    final_json_report = [item.to_dict() for item in report.values()]
    return api_response(data=final_json_report)
