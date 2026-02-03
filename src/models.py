from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

from .constants import DownloadStatus

db = SQLAlchemy()


class Download(db.Model):  # type: ignore[name-defined]
    __tablename__ = "downloads"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.Integer, nullable=True)

    order_number = db.Column(db.Integer, default=0)

    start_time = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    end_time = db.Column(db.DateTime, nullable=True)
    # TODO: update col name at next migration
    updated_at = db.Column(
        db.DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )

    status = db.Column(db.Integer, default=DownloadStatus.PENDING, nullable=False)
    # TODO: update name to use full word
    status_msg = db.Column(db.Text, nullable=True)

    @property
    def start_time_iso(self):
        return self.start_time.isoformat() + "Z" if self.start_time else None

    @property
    def end_time_iso(self):
        return self.end_time.isoformat() + "Z" if self.end_time else None

    @property
    def updated_time_iso(self):
        return self.updated_at.isoformat() + "Z" if self.updated_at else None
