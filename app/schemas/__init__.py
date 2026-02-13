from marshmallow import fields, validate

from app.constants import DownloadStatus, MediaType


class TitleField(fields.Str):
    """A reusable field for title validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("allow_none", True)
        super().__init__(**kwargs)


class MediaTypeField(fields.Int):
    """A reusable field for MediaType validation and formatting."""

    def __init__(self, **kwargs):
        kwargs.setdefault("data_key", "mediaType")
        kwargs.setdefault("allow_none", True)
        kwargs.setdefault("validate", validate.OneOf([e.value for e in MediaType]))
        kwargs.setdefault("strict", True)
        super().__init__(**kwargs)


class DownloadStatusField(fields.Int):
    """A reusable field for DownloadStatus validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("allow_none", True)
        kwargs.setdefault("validate", validate.OneOf([e.value for e in DownloadStatus]))
        kwargs.setdefault("strict", True)
        super().__init__(**kwargs)
