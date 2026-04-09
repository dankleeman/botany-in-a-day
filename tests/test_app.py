from unittest.mock import patch

from app import _is_dark, _theme_css, app
from config import Config


def test_index_redirects():
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/quiz" in resp.headers["Location"]


def test_quiz_shows_question():
    fake_question = {
        "family": "Asteraceae",
        "common": "Aster / Sunflower Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Daisy (Bellis perennis)",
        "attribution": "CC BY Someone",
        "obs_url": "https://inaturalist.org/observations/1",
    }
    with patch("app.load_question", return_value=fake_question):
        with app.test_client() as client:
            resp = client.get("/quiz")
            assert resp.status_code == 200
            assert b"Which family does this plant belong to?" in resp.data


def test_quiz_handles_no_question():
    with patch("app.load_question", return_value=None):
        with app.test_client() as client:
            resp = client.get("/quiz")
            assert resp.status_code == 200
            assert b"Try Again" in resp.data


def test_answer_correct():
    fake_question = {
        "family": "Rosaceae",
        "common": "Rose Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Rosa canina",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["score"] = 0
            sess["total"] = 0
            sess["question_num"] = 1
        resp = client.post("/answer", data={"answer": "Rosaceae"})
        assert resp.status_code == 200
        assert b"Correct!" in resp.data


def test_answer_wrong():
    fake_question = {
        "family": "Rosaceae",
        "common": "Rose Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Rosa canina",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["score"] = 0
            sess["total"] = 0
            sess["question_num"] = 1
        resp = client.post("/answer", data={"answer": "Fabaceae"})
        assert resp.status_code == 200
        assert b"Wrong" in resp.data


def test_answer_tracks_family_stats():
    fake_question = {
        "family": "Rosaceae",
        "common": "Rose Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Rosa canina",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["score"] = 0
            sess["total"] = 0
            sess["question_num"] = 1
            sess["family_stats"] = {}
        client.post("/answer", data={"answer": "Rosaceae"})
        with client.session_transaction() as sess:
            assert sess["family_stats"]["Rosaceae"]["correct"] == 1
            assert sess["family_stats"]["Rosaceae"]["total"] == 1
        # Wrong answer
        with client.session_transaction() as sess:
            sess["current"] = fake_question
        client.post("/answer", data={"answer": "Fabaceae"})
        with client.session_transaction() as sess:
            assert sess["family_stats"]["Rosaceae"]["correct"] == 1
            assert sess["family_stats"]["Rosaceae"]["total"] == 2


def test_answer_skip_does_not_track_stats():
    fake_question = {
        "family": "Rosaceae",
        "common": "Rose Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Rosa canina",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["score"] = 0
            sess["total"] = 0
            sess["question_num"] = 1
            sess["family_stats"] = {}
        client.post("/answer", data={"answer": "_skip"})
        with client.session_transaction() as sess:
            assert sess.get("family_stats", {}) == {}


def test_stats_page_empty():
    with app.test_client() as client:
        resp = client.get("/stats")
        assert resp.status_code == 200
        assert b"Families" in resp.data


def test_stats_page_with_data():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["score"] = 3
            sess["total"] = 5
            sess["family_stats"] = {
                "Rosaceae": {"correct": 2, "total": 3},
                "Fabaceae": {"correct": 1, "total": 2},
            }
        resp = client.get("/stats")
        assert resp.status_code == 200
        assert b"Rosaceae" in resp.data
        assert b"Fabaceae" in resp.data


def test_answer_skip():
    fake_question = {
        "family": "Rosaceae",
        "common": "Rose Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Rosa canina",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["score"] = 0
            sess["total"] = 0
            sess["question_num"] = 1
        resp = client.post("/answer", data={"answer": "_skip"})
        assert resp.status_code == 200
        assert b"Skipped" in resp.data


def test_toggle_theme():
    with app.test_client() as client:
        # Default is light
        resp = client.get("/toggle-theme")
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess["theme"] == "dark"
        # Toggle back
        client.get("/toggle-theme")
        with client.session_transaction() as sess:
            assert sess["theme"] == "light"


def test_dark_theme_renders():
    fake_question = {
        "family": "Asteraceae",
        "common": "Aster / Sunflower Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Daisy (Bellis perennis)",
        "attribution": "",
        "obs_url": "",
    }
    with patch("app.load_question", return_value=fake_question):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["theme"] = "dark"
            resp = client.get("/quiz")
            assert resp.status_code == 200
            assert b"#1a1a2e" in resp.data


def test_answer_no_current_redirects():
    with app.test_client() as client:
        resp = client.post("/answer", data={"answer": "Rosaceae"})
        assert resp.status_code == 302
        assert "/quiz" in resp.headers["Location"]


def test_toggle_theme_from_stats():
    with app.test_client() as client:
        resp = client.get("/toggle-theme", headers={"Referer": "http://localhost/stats"})
        assert resp.status_code == 302
        assert "/stats" in resp.headers["Location"]


def test_quiz_keep_reuses_current_question():
    fake_question = {
        "family": "Asteraceae",
        "common": "Aster / Sunflower Family",
        "photo_url": "https://example.com/medium.jpg",
        "species": "Daisy (Bellis perennis)",
        "attribution": "",
        "obs_url": "",
    }
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["current"] = fake_question
            sess["question_num"] = 3
            sess["score"] = 1
            sess["total"] = 2
        resp = client.get("/quiz?keep=1")
        assert resp.status_code == 200
        assert b"Asteraceae" in resp.data
        with client.session_transaction() as sess:
            # question_num should not increment
            assert sess["question_num"] == 3


def test_update_families():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["active_families"] = ["Rosaceae", "Fabaceae"]
        resp = client.post(
            "/update-families",
            data={"families": ["Rosaceae", "Asteraceae", "Poaceae"]},
        )
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sorted(sess["active_families"]) == ["Asteraceae", "Poaceae", "Rosaceae"]


def test_update_families_ignores_invalid():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["active_families"] = ["Rosaceae"]
        client.post(
            "/update-families",
            data={"families": ["Rosaceae", "NotAFamily"]},
        )
        with client.session_transaction() as sess:
            assert sess["active_families"] == ["Rosaceae"]


def test_update_families_empty_keeps_current():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["active_families"] = ["Rosaceae"]
        client.post("/update-families", data={})
        with client.session_transaction() as sess:
            assert sess["active_families"] == ["Rosaceae"]


def test_stats_page_respects_dark_theme():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["theme"] = "dark"
            sess["score"] = 1
            sess["total"] = 1
            sess["family_stats"] = {"Rosaceae": {"correct": 1, "total": 1}}
        resp = client.get("/stats")
        assert resp.status_code == 200
        assert b"#1a1a2e" in resp.data


# --- _is_dark unit tests ---


def test_is_dark_returns_true_for_dark_bg():
    assert _is_dark({"bg": "#1a1a2e"}) is True


def test_is_dark_returns_false_for_light_bg():
    assert _is_dark({"bg": "#f5f0e8"}) is False


def test_is_dark_returns_false_for_non_six_char_hex():
    # Covers the else branch (len != 6)
    assert _is_dark({"bg": "#fff"}) is False
    assert _is_dark({"bg": "#aabbccdd"}) is False


def test_is_dark_midpoint_boundary():
    # Average exactly 128 → not dark (< 128 is the condition)
    assert _is_dark({"bg": "#808080"}) is False
    assert _is_dark({"bg": "#7f7f7f"}) is True


# --- _theme_css unit tests ---

_LIGHT_THEME = {"bg": "#fff", "text": "#000", "accent": "#0f0", "accent_hover": "#0a0"}
_DARK_THEME = {"bg": "#111111", "text": "#eeeeee", "accent": "#66ff66", "accent_hover": "#55ff55"}


def test_theme_css_contains_all_custom_properties():
    css = _theme_css(_LIGHT_THEME)
    for prop in ("--bg", "--text", "--accent", "--accent-hover", "--btn-bg", "--muted", "--shadow"):
        assert prop in css, f"missing {prop}"


def test_theme_css_light_uses_white_button_bg():
    css = _theme_css(_LIGHT_THEME)
    assert "white" in css


def test_theme_css_dark_uses_dark_button_bg():
    css = _theme_css(_DARK_THEME)
    assert "white" not in css


# --- config-override integration tests ---

_BASE_CONFIG = dict(
    secret_key="test",
    batch_size=20,
    place_id="97394",
    flowering_only=True,
    theme_bg="",
    theme_text="",
    theme_accent="",
    theme_accent_hover="",
    debug=False,
    build_version="",
)


def test_build_version_shown_in_debug_mode():
    cfg = Config(**{**_BASE_CONFIG, "debug": True, "build_version": "v9.9.9"})
    fake_q = {
        "family": "Asteraceae",
        "common": "Aster",
        "photo_url": "https://example.com/m.jpg",
        "species": "Daisy",
        "attribution": "",
        "obs_url": "",
    }
    with patch("app.config", cfg), patch("app.load_question", return_value=fake_q):
        with app.test_client() as client:
            resp = client.get("/quiz")
    assert b"v9.9.9" in resp.data


def test_build_version_hidden_when_not_debug():
    cfg = Config(**{**_BASE_CONFIG, "debug": False, "build_version": "v9.9.9"})
    fake_q = {
        "family": "Asteraceae",
        "common": "Aster",
        "photo_url": "https://example.com/m.jpg",
        "species": "Daisy",
        "attribution": "",
        "obs_url": "",
    }
    with patch("app.config", cfg), patch("app.load_question", return_value=fake_q):
        with app.test_client() as client:
            resp = client.get("/quiz")
    assert b"v9.9.9" not in resp.data


def test_theme_bg_override_applied_to_render():
    cfg = Config(**{**_BASE_CONFIG, "theme_bg": "#abcdef"})
    fake_q = {
        "family": "Asteraceae",
        "common": "Aster",
        "photo_url": "https://example.com/m.jpg",
        "species": "Daisy",
        "attribution": "",
        "obs_url": "",
    }
    with patch("app.config", cfg), patch("app.load_question", return_value=fake_q):
        with app.test_client() as client:
            resp = client.get("/quiz")
    assert b"#abcdef" in resp.data


def test_theme_locked_when_config_has_overrides():
    cfg = Config(**{**_BASE_CONFIG, "theme_bg": "#abcdef"})
    fake_q = {
        "family": "Asteraceae",
        "common": "Aster",
        "photo_url": "https://example.com/m.jpg",
        "species": "Daisy",
        "attribution": "",
        "obs_url": "",
    }
    with patch("app.config", cfg), patch("app.load_question", return_value=fake_q):
        with app.test_client() as client:
            resp = client.get("/quiz")
    # Theme toggle button should be hidden when locked
    assert b"toggle-theme" not in resp.data


def test_toggle_theme_from_quiz_appends_keep():
    with app.test_client() as client:
        resp = client.get("/toggle-theme", headers={"Referer": "http://localhost/quiz"})
    assert "?keep=1" in resp.headers["Location"]


def test_toggle_theme_from_quiz_with_existing_query_no_double_keep():
    with app.test_client() as client:
        resp = client.get(
            "/toggle-theme", headers={"Referer": "http://localhost/quiz?keep=1"}
        )
    assert resp.headers["Location"].count("?") == 1


def test_index_resets_session_state():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["score"] = 5
            sess["total"] = 10
            sess["question_num"] = 3
            sess["family_stats"] = {"Rosaceae": {"correct": 2, "total": 3}}
        client.get("/")
        with client.session_transaction() as sess:
            assert sess["score"] == 0
            assert sess["total"] == 0
            assert sess["question_num"] == 0
            assert sess["family_stats"] == {}
