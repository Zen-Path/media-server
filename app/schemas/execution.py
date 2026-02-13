from marshmallow import Schema, fields, validate

from app.schemas import MediaTypeField


class DownloadRequestSchema(Schema):
    urls = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    media_type = MediaTypeField()
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
