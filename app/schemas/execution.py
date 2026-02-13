from marshmallow import Schema, fields, validate

from app.schemas import MediaTypeField, RangeField, TitleField


class DownloadItemSchema(Schema):
    """Validates an individual item inside the download request items list."""

    url = fields.URL(required=True)
    title = TitleField()
    media_type = MediaTypeField()


class DownloadRequestSchema(Schema):
    """Validates the overall media download request."""

    items = fields.List(
        fields.Nested(DownloadItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    range_start = RangeField(data_key="rangeStart")
    range_end = RangeField(data_key="rangeEnd")
