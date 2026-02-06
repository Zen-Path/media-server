import tomllib
from pathlib import Path


def get_version():
    script_dir = Path(__file__).resolve().parent
    path = script_dir / "../pyproject.toml"

    with path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


PKG_VERSION = get_version()
