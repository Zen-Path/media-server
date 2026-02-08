from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional


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


@dataclass
class OperationResult:
    status: bool
    data: Any  # Usually the ID (int)
    error: Optional[str] = None

    def get_overall_status(self) -> bool:
        """
        Returns True if the operation was successful.
        If data is a list of OperationResults, returns True if ANY are successful.
        """
        if not isinstance(self.data, list):
            return self.status

        for result in self.data:
            # Recursively check if any child result succeeded
            if isinstance(result, OperationResult):
                if result.status:
                    return True

        return False

    def to_dict(self):
        data_serialized = self.data
        if isinstance(self.data, list):
            data_serialized = [
                asdict(r) if isinstance(r, OperationResult) else r for r in self.data
            ]

        return {
            "status": self.get_overall_status(),
            "error": self.error,
            "data": data_serialized,
        }


def to_camel_case(snake_str):
    if not snake_str:
        return snake_str

    leading_count = len(snake_str) - len(snake_str.lstrip("_"))
    trailing_count = len(snake_str) - len(snake_str.rstrip("_"))

    if leading_count == len(snake_str):
        return snake_str

    # Note: We use None in the slice if trailing_count is 0,
    # because slicing [x:-0] returns an empty string in Python.
    middle = snake_str[leading_count : -trailing_count if trailing_count else None]

    # This logic collapses multiple underscores (user__name -> userName)
    components = middle.split("_")
    camel_middle = components[0] + "".join(x.title() for x in components[1:])

    return ("_" * leading_count) + camel_middle + ("_" * trailing_count)


def recursive_camelize(data):
    if isinstance(data, dict):
        return {to_camel_case(k): recursive_camelize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [recursive_camelize(i) for i in data]
    return data
