from datetime import datetime, timezone
from typing import Optional, Tuple

from common.logger import logger
from flask import current_app
from scripts.media_server.app.constants import (
    DownloadStatus,
    EventType,
)
from scripts.media_server.app.extensions import db
from scripts.media_server.app.models.download import Download


def get_all_downloads():
    """Fetches all downloads ordered by ID descending."""
    return Download.query.order_by(Download.id.desc()).all()


def get_download_by_id(download_id: int) -> Download | None:
    """Fetches a single download."""
    return Download.query.get(download_id)


def initialize_download(
    url: str, media_type: Optional[int]
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Initializes a download record and announces it.

    Returns:
        A tuple of (success_status, generated_id, error_message).
    """
    try:
        record = Download(url=url, media_type=media_type)
        db.session.add(record)
        db.session.commit()

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.CREATE, [record.to_dict()]
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, record.id, None

    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to initialize download record: {e}"
        logger.error(err_msg)
        return False, None, err_msg


def finalize_download(
    download_id: int, title: Optional[str], status: DownloadStatus
) -> Tuple[bool, Optional[str]]:
    """
    Updates a download record with final data and announces it.

    Returns:
        A tuple of (success_status, error_message).
    """
    try:
        record = db.session.get(Download, download_id)
        if not record:
            return False, f"Download ID {download_id} not found."

        record.title = title
        record.end_time = int(datetime.now(timezone.utc).timestamp())
        record.status = status

        db.session.commit()

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.UPDATE, [record.to_dict()]
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, None

    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to finalize download record #{download_id}: {e}"
        logger.error(err_msg)
        return False, err_msg
