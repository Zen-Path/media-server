from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import current_app

from app.constants import EventType
from app.extensions import db
from app.models.download import Download
from app.utils.logger import logger


def get_all_downloads():
    """Fetches all downloads ordered by ID descending."""
    return Download.query.order_by(Download.id.desc()).all()


def get_download_by_id(download_id: int) -> Download | None:
    """Fetches a single download."""
    return Download.query.get(download_id)


def bulk_update_downloads(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Updates multiple downloads.

    Ignores duplicates.
    Returns: A list of result dictionaries:
        [
            {
                "id": 1,
                "status": True,
                "updates": {"title": "New Title", "mediaType": "audio"}
            },
            {
                "id": 99,
                "status": False,
                "error": "ID not found"
            }
        ]
    """
    updates_map = {item["id"]: item for item in updates}
    existing_records = Download.query.filter(Download.id.in_(updates_map.keys())).all()

    results = []
    any_changes = False

    for target in existing_records:
        item = updates_map[target.id]
        applied_updates = {}

        # We can trust 'item' because Marshmallow already validated it.
        for key, new_value in item.items():
            if key == "id":
                continue

            if not hasattr(target, key):
                continue

            # Normalize value (handle Enums vs ints)
            db_value = new_value.value if hasattr(new_value, "value") else new_value

            current_value = getattr(target, key)

            if current_value != db_value:
                setattr(target, key, db_value)

                # Generate CamelCase key for response
                components = key.split("_")
                camel_key = components[0] + "".join(x.title() for x in components[1:])

                applied_updates[camel_key] = new_value

        if applied_updates:
            any_changes = True

        results.append(
            {
                "id": target.id,
                "status": True,
                "updates": applied_updates,
            }
        )

    found_ids = {d.id for d in existing_records}
    missing_ids = set(updates_map.keys()) - found_ids

    for missing_id in missing_ids:
        results.append(
            {
                "id": missing_id,
                "status": False,
                "error": "ID not found",
            }
        )

    if any_changes:
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
    url: str, media_type: int | None
) -> tuple[bool, int | None, str | None]:
    """
    Creates a 'shell' record in the DB and announces it.
    Returns:
        A tuple of (success_status, generated_id, error_message).
    """
    try:
        new_download = Download(url=url, media_type=media_type)
        db.session.add(new_download)
        db.session.commit()

        try:
            current_app.config["ANNOUNCER"].announce(
                EventType.CREATE, new_download.to_dict()
            )
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, new_download.id, None

    except Exception as e:
        db.session.rollback()
        return False, None, str(e)


def finalize_download(
    download_id: int, title: str | None, status: int
) -> tuple[bool, str | None]:
    """
    Updates the record with final data and announces it.
    Returns:
        A tuple of (success_status, error_message).
    """
    try:
        record = Download.query.get(download_id)
        if not record:
            return False, f"Download ID {download_id} not found."

        record.title = title
        record.status = status
        record.end_time = int(datetime.now(timezone.utc).timestamp())

        db.session.commit()

        try:
            current_app.config["ANNOUNCER"].announce(EventType.UPDATE, record.to_dict())
        except Exception as e:
            logger.warning(f"Announcer failed: {e}")

        return True, None

    except Exception as e:
        db.session.rollback()
        return False, str(e)
