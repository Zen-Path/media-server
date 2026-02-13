import json
from typing import Any, Dict, Union

from colorama import Fore, Style


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncates text and appends a notice if it exceeds max_length."""
    if not isinstance(text, str):
        text = str(text)
    if len(text) > max_length:
        return text[:max_length] + "\n... (truncated)"
    return text


def format_payload(data: Any, max_length: int = 1000, indent: int = 4) -> str:
    """Formats data to JSON if possible, then truncates it."""
    if isinstance(data, (dict, list)):
        try:
            formatted = json.dumps(data, indent=indent, ensure_ascii=False)
            return truncate_text(formatted, max_length)
        except Exception:
            return truncate_text(str(data), max_length)
    return truncate_text(str(data), max_length)


def build_request_log(
    params: Dict[str, Any], body: Union[Dict, str, None], max_length: int = 1000
) -> str:
    """Constructs the formatted request log string."""
    output_lines = []

    if params:
        # Shallow copy to avoid mutating actual request args
        safe_params = params.copy()
        if "apiKey" in safe_params:
            safe_params["apiKey"] = "***"

        params_str = format_payload(safe_params, max_length)
        output_lines.append(
            f"{Fore.LIGHTYELLOW_EX}params: {Fore.LIGHTBLACK_EX}{params_str}"
        )

    if body:
        body_str = format_payload(body, max_length)
        output_lines.append(
            f"{Fore.LIGHTYELLOW_EX}body: {Fore.LIGHTBLACK_EX}{body_str}"
        )

    if not output_lines:
        return ""

    return f"{Fore.LIGHTBLUE_EX}REQUEST:\n{'\n'.join(output_lines)}{Style.RESET_ALL}"


def build_response_log(
    method: str, path: str, duration: float, data: Any, max_length: int = 1000
) -> str:
    """Constructs the formatted response log string."""
    data_str = format_payload(data, max_length)
    return (
        f"{Fore.LIGHTBLUE_EX}RESPONSE: {Fore.LIGHTBLACK_EX}"
        f"{method} {path} (duration: {duration:.4f}s):\n"
        f"{data_str}{Style.RESET_ALL}"
    )
