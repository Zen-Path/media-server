from pathlib import Path
from typing import Any, Dict, List, Optional

from app.extensions import db
from app.models.download import Download
from app.utils.logger import logger
from scripts.demo_downloads import get_demo_downloads


def init_db(app):
    """
    Initializes the database schema using SQLAlchemy.
    """
    # Extract the path from the URI (stripping sqlite:///)
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with app.app_context():
            db.create_all()
            logger.debug("SQLAlchemy schema initialized.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise


def seed_db(
    data: Optional[List[Dict[str, Any]]] = None, row_count: Optional[int] = None
):
    """
    Seeds the database with provided data.
    """
    data_to_use = data if data is not None else get_demo_downloads(row_count=row_count)

    defaults = {
        "url": "https://default.com/media",
    }

    entries: List[Download] = [Download(**{**defaults, **row}) for row in data_to_use]

    try:
        db.session.add_all(entries)
        db.session.flush()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding database: {e}")
        raise

    return entries
