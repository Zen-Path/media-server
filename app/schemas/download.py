from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.schemas import DownloadStatusField, MediaTypeField, TitleField


class GetDownloadsQuerySchema(Schema):
    """Schema for validating query parameters when getting Downloads."""

    # Ignore unknown fields since we have to pass 'apiKey' for api requests
    class Meta:
        unknown = EXCLUDE

    ids = fields.List(fields.Int(), required=False)

    @pre_load
    def parse_comma_separated_ids(self, in_data, **kwargs):
        """Splits a comma-separated string into a list before validation."""
        # request.args in Flask is an ImmutableMultiDict, so we convert it to
        # a standard dict
        data = in_data.to_dict() if hasattr(in_data, "to_dict") else in_data.copy()

        if "ids" in data and isinstance(data["ids"], str):
            # Handle edge cases where the user passes an empty string like "?ids="
            if not data["ids"].strip():
                data["ids"] = []
            else:
                data["ids"] = data["ids"].split(",")

        return data


class DownloadUpdateSchema(Schema):
    """Schema for validating an update item for a Download instance."""

    id = fields.Integer(required=True, strict=True)
    title = TitleField()
    media_type = MediaTypeField()
    status = DownloadStatusField()


class BulkDeleteSchema(Schema):
    ids = fields.List(
        fields.Int(strict=True), required=True, validate=validate.Length(min=1)
    )
