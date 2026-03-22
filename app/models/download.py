from datetime import datetime, timezone

from app.constants import DownloadStatus
from app.extensions import db


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
