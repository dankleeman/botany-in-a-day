from unittest.mock import patch

from config import Config


def test_defaults():
    with patch.dict("os.environ", {}, clear=True):
        c = Config.from_env()
    assert c.batch_size == 20
    assert c.place_id == "97394"
    assert c.flowering_only is True
    assert c.secret_key == ""
    assert c.theme_overrides == {}
    assert c.has_theme_overrides is False


def test_custom_values():
    env = {
        "SECRET_KEY": "test-secret",
        "BATCH_SIZE": "50",
        "PLACE_ID": "1234",
        "FLOWERING_ONLY": "false",
    }
    with patch.dict("os.environ", env, clear=True):
        c = Config.from_env()
    assert c.secret_key == "test-secret"
    assert c.batch_size == 50
    assert c.place_id == "1234"
    assert c.flowering_only is False


def test_flowering_only_truthy_values():
    for value in ("true", "True", "TRUE", "1", "yes", "Yes"):
        with patch.dict("os.environ", {"FLOWERING_ONLY": value}, clear=True):
            c = Config.from_env()
        assert c.flowering_only is True, f"Expected True for '{value}'"


def test_flowering_only_falsy_values():
    for value in ("false", "0", "no", "anything"):
        with patch.dict("os.environ", {"FLOWERING_ONLY": value}, clear=True):
            c = Config.from_env()
        assert c.flowering_only is False, f"Expected False for '{value}'"


def test_theme_overrides_partial():
    env = {"THEME_BG": "#000", "THEME_ACCENT": "#f00"}
    with patch.dict("os.environ", env, clear=True):
        c = Config.from_env()
    assert c.theme_overrides == {"bg": "#000", "accent": "#f00"}
    assert c.has_theme_overrides is True


def test_theme_overrides_full():
    env = {
        "THEME_BG": "#000",
        "THEME_TEXT": "#fff",
        "THEME_ACCENT": "#f00",
        "THEME_ACCENT_HOVER": "#f55",
    }
    with patch.dict("os.environ", env, clear=True):
        c = Config.from_env()
    assert c.theme_overrides == {
        "bg": "#000",
        "text": "#fff",
        "accent": "#f00",
        "accent_hover": "#f55",
    }
