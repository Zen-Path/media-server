from marshmallow import Schema, fields, validate

from app.constants import MediaType


class DownloadRequestSchema(Schema):
    urls = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    media_type = fields.Enum(MediaType, data_key="mediaType", load_default=None)
    range_start = fields.Int(data_key="rangeStart", load_default=None)
    range_end = fields.Int(data_key="rangeEnd", load_default=None)
