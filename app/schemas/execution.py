from marshmallow import Schema, fields, validate

from app.constants import MediaType


class DownloadRequestSchema(Schema):
    urls = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    media_type = fields.Int(
        data_key="mediaType",
        allow_none=True,
        validate=validate.OneOf([e.value for e in MediaType]),
        strict=True,
    )
    range_start = fields.Int(
        data_key="rangeStart",
        load_default=None,
        strict=True,
    )
    range_end = fields.Int(
        data_key="rangeEnd",
        load_default=None,
        strict=True,
    )
