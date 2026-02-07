import re
from abc import ABC, abstractmethod
from typing import List, Optional

from common.helpers import run_command
from flask import current_app
from scripts.media_server.app.utils.tools import DownloadReportItem


class Media(ABC):
    @classmethod
    @abstractmethod
    def download(
        cls,
        urls: List[str],
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
    ) -> DownloadReportItem:
        pass


class Gallery(Media):
    ERROR_PATTERNS = [
        (
            r"^\[[^\]]+\]\[info\] No results for",
            "[gallery-dl] No results found for url.",
        ),
        (
            r"^\[[^\]]+\]\[warning\] File size larger",
            "[gallery-dl] File size larger than allowed.",
        ),
        (
            r"^\[[^\]]+\]\[error\]",
            lambda line: f"[gallery-dl] Error: {line.split(']')[-1].strip()}",
        ),
    ]

    @classmethod
    def download(
        cls,
        urls: List[str],
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
    ) -> DownloadReportItem:
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

        cmd_result = run_command(command)

        report = DownloadReportItem()
        report.output = cmd_result.output

        if cmd_result.return_code != 0:
            report.status = False
            report.error = (
                f"[gallery-dl] System command failed (Code {cmd_result.return_code})"
            )
            return report

        report.status = True

        for line in report.output.splitlines():
            line = line.strip()
            if not line:
                continue

            # CHeck for downloaded files
            if line.startswith(("/", "./", "# ")):
                clean_path = line.lstrip("# ").strip()
                report.files.append(clean_path)
                continue

            # Check for known error patterns
            for pattern, handler in cls.ERROR_PATTERNS:
                if re.search(pattern, line):
                    report.status = False

                    if callable(handler):
                        report.error = str(handler(line))  # str for mypy
                    else:
                        report.error = handler

                    return report

        return report
