from marshmallow import Schema, fields, validate

from app.schemas import DownloadStatusField, MediaTypeField, TitleField


class DownloadUpdateBaseSchema(Schema):
    """Schema for validating editable fields of a Download instance."""

    title = TitleField()
    media_type = MediaTypeField()
    status = DownloadStatusField()


class DownloadBulkUpdateSchema(DownloadUpdateBaseSchema):
    """Schema for a batch update item, requiring an explicit ID"""

    id = fields.Integer(required=True, strict=True)


class BulkDeleteSchema(Schema):
    ids = fields.List(
        fields.Int(strict=True), required=True, validate=validate.Length(min=1)
    )
