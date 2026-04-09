import os

from flask import Flask, redirect, render_template, request, session, url_for

from config import config
from families import DEFAULT_FAMILIES, FAMILIES
from inat import load_question

app = Flask(__name__)
app.secret_key = config.secret_key or os.urandom(24)

THEMES = {
    "light": {
        "bg": "#f5f0e8",
        "text": "#333",
        "accent": "#2d5016",
        "accent_hover": "#3d6b20",
    },
    "dark": {
        "bg": "#1a1a2e",
        "text": "#e0e0e0",
        "accent": "#6abf5e",
        "accent_hover": "#8ad680",
    },
}


def _get_theme() -> dict:
    name = session.get("theme", "light")
    theme = dict(THEMES.get(name, THEMES["light"]))
    theme.update(config.theme_overrides)
    return theme


def _theme_css(theme: dict) -> str:
    dark = _is_dark(theme)
    return f"""
        :root {{
            --bg: {theme["bg"]};
            --text: {theme["text"]};
            --accent: {theme["accent"]};
            --accent-hover: {theme["accent_hover"]};
            --btn-bg: {"#2a2a3e" if dark else "white"};
            --btn-border: {"#4a8a3e" if dark else "#8aad6e"};
            --btn-hover-bg: {"#353550" if dark else "#e8f5d8"};
            --muted: {"#aaa" if dark else "#666"};
            --muted2: {"#888" if dark else "#888"};
            --shadow: {"rgba(0,0,0,0.3)" if dark else "rgba(0,0,0,0.15)"};
            --correct-bg: {"#1a3a1a" if dark else "#d4edda"};
            --correct-border: {"#4a8a3e" if dark else "#8aad6e"};
            --wrong-bg: {"#3a1a1a" if dark else "#f8d7da"};
            --wrong-border: {"#8a4a4a" if dark else "#d9828a"};
            --skip-bg: {"#3a3a1a" if dark else "#fff3cd"};
            --skip-border: {"#8a8a3a" if dark else "#c9b458"};
            --bar-bg: {"#3a3a4e" if dark else "#e0e0e0"};
            --table-border: {"#3a3a4e" if dark else "#ddd"};
        }}
    """


def _is_dark(theme: dict) -> bool:
    """Heuristic: dark themes have a dark background."""
    bg = theme["bg"].lstrip("#")
    if len(bg) == 6:
        r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
        return (r + g + b) / 3 < 128
    return False


def _render(template, **kwargs):
    theme = _get_theme()
    return render_template(
        template,
        theme_css=_theme_css(theme),
        is_dark=_is_dark(theme),
        theme_locked=config.has_theme_overrides,
        build_version=config.build_version if config.debug else "",
        active_families=session.get("active_families", DEFAULT_FAMILIES),
        **kwargs,
    )


#################################################


@app.route("/")
def index():
    session["score"] = 0
    session["total"] = 0
    session["question_num"] = 0
    session["family_stats"] = {}
    session["active_families"] = DEFAULT_FAMILIES
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    question = session.get("current") if request.args.get("keep") else None
    if not question:
        question = load_question(session.get("active_families"))
    if not question:
        return _render(
            "quiz.html",
            error="Couldn't load a photo from iNaturalist. Try again.",
            question_num=session.get("question_num", 0),
            score=session.get("score", 0),
            total=session.get("total", 0),
            result=None,
            photo_url="",
            families=FAMILIES,
            correct_family="",
            correct_common="",
            species="",
            chosen_family="",
            attribution="",
            obs_url="",
        )

    if not request.args.get("keep"):
        session["current"] = question
        session["question_num"] = session.get("question_num", 0) + 1

    return _render(
        "quiz.html",
        photo_url=question["photo_url"],
        families=FAMILIES,
        question_num=session["question_num"],
        score=session.get("score", 0),
        total=session.get("total", 0),
        result=None,
        error=None,
        correct_family="",
        correct_common="",
        species="",
        chosen_family="",
        attribution=question["attribution"],
        obs_url=question["obs_url"],
    )


@app.route("/answer", methods=["POST"])
def answer():
    current = session.get("current")
    if not current:
        return redirect(url_for("quiz"))

    chosen = request.form.get("answer", "")
    skipped = chosen == "_skip"

    if skipped:
        result = "skip"
    else:
        result = chosen == current["family"]
        session["total"] = session.get("total", 0) + 1
        if result:
            session["score"] = session.get("score", 0) + 1

        family = current["family"]
        family_stats = session.get("family_stats", {})
        stats = family_stats.get(family, {"correct": 0, "total": 0})
        stats["total"] += 1
        if result:
            stats["correct"] += 1
        family_stats[family] = stats
        session["family_stats"] = family_stats

    return _render(
        "quiz.html",
        photo_url=current["photo_url"],
        result=result,
        correct_family=current["family"],
        correct_common=current["common"],
        species=current["species"],
        chosen_family=chosen,
        question_num=session.get("question_num", 0),
        score=session.get("score", 0),
        total=session.get("total", 0),
        families=FAMILIES,
        error=None,
        attribution=current.get("attribution", ""),
        obs_url=current.get("obs_url", ""),
    )


@app.route("/stats")
def stats():
    return _render(
        "stats.html",
        score=session.get("score", 0),
        total=session.get("total", 0),
        family_stats=session.get("family_stats", {}),
        families=FAMILIES,
    )


@app.route("/update-families", methods=["POST"])
def update_families():
    selected = request.form.getlist("families")
    # Only allow families that exist in the TOML
    valid = [f for f in selected if f in FAMILIES]
    if valid:
        session["active_families"] = valid
    return redirect(url_for("stats"))


@app.route("/toggle-theme")
def toggle_theme():
    current = session.get("theme", "light")
    session["theme"] = "dark" if current == "light" else "light"
    referrer = request.referrer or url_for("quiz")
    if "/quiz" in referrer and "?" not in referrer:
        referrer += "?keep=1"
    return redirect(referrer)
