import re
from abc import ABC, abstractmethod
from typing import List, Optional

from flask import current_app

from app.utils.tools import DownloadReportItem, run_command


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

        lines = cmd_result.output.splitlines()
        filtered_output = []

        # Extract files & clean output
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith(("/", "./", "# ")):
                clean_path = line.lstrip("# ").strip()
                report.files.append(clean_path)
            else:
                # Keep non-file lines for the log
                filtered_output.append(line)

        report.output = "\n".join(filtered_output)

        if cmd_result.return_code != 0:
            report.status = False
            report.error = (
                f"[gallery-dl] System command failed (Code {cmd_result.return_code})"
            )

        # Known error patterns should override the generic "system failed" error
        for line in lines:
            for pattern, handler in cls.ERROR_PATTERNS:
                if re.search(pattern, line):
                    report.status = False

                    if callable(handler):
                        report.error = str(handler(line))
                    else:
                        report.error = str(handler)

                    # If we matched a specific error, return immediately
                    return report

        return report
