from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class DownloadReportItem:
    url: Optional[str] = None
    status: bool = True
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    log: str = ""
    output: str = ""
    files: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def to_camel_case(snake_str):
    if not snake_str:
        return snake_str

    leading_count = len(snake_str) - len(snake_str.lstrip("_"))
    trailing_count = len(snake_str) - len(snake_str.rstrip("_"))

    # For strings that are only underscores (e.g "___")
    if leading_count == len(snake_str):
        return snake_str

    middle = snake_str[leading_count : -trailing_count if trailing_count else None]

    # If there's no underscore, we assume camel case, for idempotency.
    if "_" not in middle:
        return snake_str

    # This logic collapses multiple underscores (user__name -> userName)
    components = middle.split("_")
    camel_middle = components[0].lower() + "".join(x.title() for x in components[1:])

    return ("_" * leading_count) + camel_middle + ("_" * trailing_count)


def recursive_camelize(data):
    if isinstance(data, dict):
        return {to_camel_case(k): recursive_camelize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [recursive_camelize(i) for i in data]
    return data
