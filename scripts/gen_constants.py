import json
import os
import sys
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

from app.constants import DownloadStatus, EventType, MediaType

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".." / ".env"
OUTPUT_FILE = BASE_DIR.parent / "shared" / "constants.js"

load_dotenv(dotenv_path=ENV_PATH)


# Map the Python object to the desired JavaScript variable name
CONSTANTS_TO_EXPORT = {
    "DOWNLOAD_STATUS": DownloadStatus,
    "MEDIA_TYPE": MediaType,
    "EVENT_TYPE": EventType,
    "SERVER_PORT": os.getenv("SERVER_PORT"),
    "API_SECRET_KEY": os.getenv("API_SECRET_KEY"),
}

# GENERATOR


def get_js_value(py_value):
    """
    intelligently converts a Python value to a JSON-compatible JS string.
    """
    # Handle Enums
    if isinstance(py_value, type) and issubclass(py_value, Enum):
        data = {member.name: member.value for member in py_value}
        return json.dumps(data, indent=4)

    # json.dumps handles everything else
    try:
        return json.dumps(py_value, indent=4)
    except TypeError as e:
        print(f"⚠️  Warning: Could not serialize {py_value}. Skipping. Error: {e}")
        return "null"


def generate():
    print("⚙️  Reading constants from Python...")

    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        print(f"📁 Creating directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    js_lines = [
        "// ------------------------------------------------------------------",
        "// AUTO-GENERATED FILE. DO NOT EDIT.",
        "// Run 'npm run gen' to update.",
        "// ------------------------------------------------------------------",
        "",
    ]

    for js_name, py_value in CONSTANTS_TO_EXPORT.items():
        js_val_str = get_js_value(py_value)

        # We use Object.freeze for objects/arrays to prevent accidental edits in JS
        if js_val_str.strip().startswith("{") or js_val_str.strip().startswith("["):
            line = f"export const {js_name} = Object.freeze({js_val_str});"
        else:
            line = f"export const {js_name} = {js_val_str};"

        js_lines.append(line)
        js_lines.append("")  # Empty line for readability

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(js_lines))
        print(
            f"✅ Successfully wrote {len(CONSTANTS_TO_EXPORT)} constants "
            f"to {OUTPUT_FILE}"
        )
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate()
