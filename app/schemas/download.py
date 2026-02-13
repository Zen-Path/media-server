from marshmallow import Schema, fields, validate

from app.schemas import DownloadStatusField, MediaTypeField, TitleField


class DownloadUpdateSchema(Schema):
    """Validates a single update entry."""

    id = fields.Int(required=True, strict=True)
    title = TitleField()
    media_type = MediaTypeField()
    status = DownloadStatusField()


class BulkDeleteSchema(Schema):
    ids = fields.List(
        fields.Int(strict=True), required=True, validate=validate.Length(min=1)
    )
