from marshmallow import fields, validate

from app.constants import MAX_TITLE_LENGTH, DownloadStatus, MediaType


class TitleField(fields.Str):
    """A reusable field for title validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("allow_none", True)
        # TODO: Instead of discarding titles that are too long, we should just trim
        # them. Would require new test cases.
        kwargs.setdefault("validate", validate.Length(max=MAX_TITLE_LENGTH))
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


class RangeField(fields.Int):
    """A reusable field for range validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("load_default", None)
        kwargs.setdefault("strict", True)
        super().__init__(**kwargs)
