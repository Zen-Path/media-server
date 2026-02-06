from datetime import datetime, timezone

from scripts.media_server.app.constants import DownloadStatus
from scripts.media_server.app.extensions import db


class Download(db.Model):  # type: ignore[name-defined]
    __tablename__ = "downloads"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.Integer, nullable=True)

    order_number = db.Column(db.Integer, default=0)

    # Storing as seconds (BigInt) avoids Year 2038 issues
    start_time = db.Column(
        db.BigInteger,
        default=lambda: int(datetime.now(timezone.utc).timestamp()),
        nullable=False,
    )

    end_time = db.Column(db.BigInteger, nullable=True)

    update_time = db.Column(
        db.BigInteger,
        nullable=True,
        onupdate=lambda: int(datetime.now(timezone.utc).timestamp()),
    )

    status = db.Column(db.Integer, default=DownloadStatus.PENDING, nullable=False)
    status_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        """
        Serializes the object to a dictionary for JSON responses.
        Converts Python snake_case to JavaScript camelCase.
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "mediaType": self.media_type,
            "orderNumber": self.order_number,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "updateTime": self.update_time,
            "status": self.status,
            "statusMessage": self.status_message,
        }
