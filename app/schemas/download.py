from marshmallow import Schema, fields, validate

from app.schemas import DownloadStatusField, MediaTypeField


class DownloadUpdateSchema(Schema):
    """Validates a single update entry."""

    id = fields.Int(required=True, strict=True)
    title = fields.Str(allow_none=True)
    media_type = MediaTypeField()
    status = DownloadStatusField()


class BulkDeleteSchema(Schema):
    ids = fields.List(
        fields.Int(strict=True), required=True, validate=validate.Length(min=1)
    )
