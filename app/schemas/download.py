from marshmallow import Schema, fields, validate
from scripts.media_server.app.constants import DownloadStatus, MediaType


class DownloadUpdateSchema(Schema):
    """
    Validates a single update entry.
    """

    id = fields.Int(required=True, strict=True)
    title = fields.Str(allow_none=True)

    media_type = fields.Int(
        data_key="mediaType",
        allow_none=True,
        validate=validate.OneOf([e.value for e in MediaType]),
        strict=True,
    )
    status = fields.Int(
        allow_none=True,
        validate=validate.OneOf([e.value for e in DownloadStatus]),
        strict=True,
    )


class BulkDeleteSchema(Schema):
    ids = fields.List(
        fields.Int(strict=True), required=True, validate=validate.Length(min=1)
    )
