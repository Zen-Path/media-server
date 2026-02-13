from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app

from app.constants import (
    DownloadStatus,
    EventType,
)
from app.extensions import db
from app.models.download import Download
from app.utils.logger import logger


def get_all_downloads():
    """Fetches all downloads ordered by ID descending."""
    return Download.query.order_by(Download.id.desc()).all()


def get_download_by_id(download_id: int) -> Download | None:
    """Fetches a single download."""
    return Download.query.get(download_id)


def bulk_edit_downloads(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process bulk updates.
    Returns a list of results with {id, status, error, updates}.
    """
    updates_map = {item["id"]: item for item in updates}
    existing_records = Download.query.filter(Download.id.in_(updates_map.keys())).all()

    results = []
    session_dirty = False

    for record in existing_records:
        new_data = updates_map[record.id]
        applied_updates = {}

        for key, new_value in new_data.items():
            if key == "id":
                continue

            # Ensure model actually has this column
            if not hasattr(record, key):
                continue

            current_value = getattr(record, key)

            is_different = False

            if hasattr(current_value, "value") and not hasattr(new_value, "value"):
                # Current is Enum, new is primitive
                if current_value.value != new_value:
                    is_different = True
            elif current_value != new_value:
                is_different = True

            if is_different:
                setattr(record, key, new_value)
                applied_updates[key] = new_value
                session_dirty = True

        results.append(
            {"id": record.id, "status": True, "updates": applied_updates, "error": None}
        )

    # Handle Missing IDs
    found_ids = {r.id for r in existing_records}
    missing_ids = set(updates_map.keys()) - found_ids

    for missing_id in missing_ids:
        results.append(
            {
                "id": missing_id,
                "status": False,
                "updates": None,
                "error": "ID not found",
            }
        )

    if session_dirty:
        db.session.commit()

    return results


def bulk_delete_downloads(ids: List[int]) -> List[int]:
    """
    Deletes downloads by ID.
    Ignores records that don't exist.

    Returns:
        List[int]: A list of IDs that were successfully found and deleted.
    """
    existing_records = Download.query.filter(Download.id.in_(ids)).all()
    existing_ids = [d.id for d in existing_records]

    if not existing_ids:
        return []

    Download.query.filter(Download.id.in_(existing_ids)).delete(
        synchronize_session=False
    )
    db.session.commit()

    return existing_ids


def initialize_download(
    url: str, media_type: Optional[int]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Initializes a download record and announces it.

    Returns:
        A tuple of (success_status, error_message, record_dict).
    """
    try:
        record = Download(url=url, media_type=media_type)
        db.session.add(record)
        db.session.commit()

        record_dict = record.to_dict()

        try:
            current_app.config["ANNOUNCER"].announce(EventType.CREATE, [record_dict])
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, None, record_dict

    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to initialize download record: {e}"
        logger.error(err_msg)
        return False, err_msg, None


def finalize_download(
    download_id: int, title: Optional[str], status: DownloadStatus
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Updates a download record with final data.

    Returns:
        A tuple of (success_status, error_message, record_dict).
    """
    try:
        record = db.session.get(Download, download_id)
        if not record:
            return False, f"Download ID {download_id} not found.", None

        record.title = title
        record.end_time = int(datetime.now(timezone.utc).timestamp())
        record.status = status

        db.session.commit()

        # Return the dictionary representation of the saved object
        return True, None, record.to_dict()

    except Exception as e:
        db.session.rollback()

        err_msg = f"Failed to finalize download record #{download_id}: {e}"
        logger.error(err_msg)
        return False, err_msg, None
