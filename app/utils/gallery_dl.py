from typing import List, Optional

from flask import current_app

from app.utils.tools import CommandResult, run_command


def download_gallery(
    urls: List[str], range_start: Optional[int], range_end: Optional[int]
) -> CommandResult:
    """
    Executes gallery-dl for the given URLs with range options.
    """
    cmd = ["gallery-dl", "--verbose"]

    if range_start is not None and range_end is not None:
        cmd.extend(["--range", f"{range_start}-{range_end}"])
    elif range_start is not None:
        cmd.extend(["--range", f"{range_start}-"])

    cmd.extend(urls)

    try:
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
    except Exception as e:
        return CommandResult(return_code=1, output=str(e))
