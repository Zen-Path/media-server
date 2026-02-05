from abc import ABC, abstractmethod
from typing import List, Optional

from common.helpers import CommandResult, run_command
from flask import current_app


class Media(ABC):
    @classmethod
    @abstractmethod
    def download(
        cls,
        urls: List[str],
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
    ) -> CommandResult:
        pass


class Gallery(Media):
    @classmethod
    def download(
        cls,
        urls: List[str],
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
    ) -> CommandResult:
        """
        Download media using 'gallery-dl'.
        """
        output_dir = current_app.config.get("DOWNLOAD_DIR", "") / "Galleries"

        command = [
            "gallery-dl",
            "-o",
            f"base-directory={output_dir}",
            "--no-colors",
            *urls,
        ]

        if range_start or range_end:
            command += ["--range", f"{range_start or 0}-{range_end or ''}"]

        return run_command(command)
