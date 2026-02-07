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
