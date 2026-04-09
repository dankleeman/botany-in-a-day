import tomllib
from pathlib import Path

_FAMILIES_PATH = Path(__file__).parent / "families.toml"


def _load_families() -> dict[str, dict]:
    with open(_FAMILIES_PATH, "rb") as f:
        data = tomllib.load(f)
    return {
        entry["name"]: {
            "common": entry["common"],
            "taxon_id": entry["taxon_id"],
            "default": entry.get("default", False),
        }
        for entry in data["family"]
    }


FAMILIES = _load_families()
FAMILY_NAMES = list(FAMILIES.keys())
DEFAULT_FAMILIES = [name for name, info in FAMILIES.items() if info["default"]]
