import os
from dataclasses import dataclass


def _parse_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class Config:
    secret_key: str
    batch_size: int
    place_id: str
    flowering_only: bool
    theme_bg: str
    theme_text: str
    theme_accent: str
    theme_accent_hover: str
    debug: bool
    build_version: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            secret_key=os.environ.get("SECRET_KEY", ""),
            batch_size=int(os.environ.get("BATCH_SIZE", "20")),
            place_id=os.environ.get("PLACE_ID", "97394"),
            flowering_only=_parse_bool(os.environ.get("FLOWERING_ONLY", "true")),
            theme_bg=os.environ.get("THEME_BG", ""),
            theme_text=os.environ.get("THEME_TEXT", ""),
            theme_accent=os.environ.get("THEME_ACCENT", ""),
            theme_accent_hover=os.environ.get("THEME_ACCENT_HOVER", ""),
            debug=_parse_bool(os.environ.get("DEBUG", "false")),
            build_version=os.environ.get("BUILD_VERSION", ""),
        )

    @property
    def theme_overrides(self) -> dict[str, str]:
        overrides = {}
        if self.theme_bg:
            overrides["bg"] = self.theme_bg
        if self.theme_text:
            overrides["text"] = self.theme_text
        if self.theme_accent:
            overrides["accent"] = self.theme_accent
        if self.theme_accent_hover:
            overrides["accent_hover"] = self.theme_accent_hover
        return overrides

    @property
    def has_theme_overrides(self) -> bool:
        return bool(self.theme_overrides)


config = Config.from_env()
