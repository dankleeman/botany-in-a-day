format:
    uv run ruff check --fix
    uv run ruff format

check:
    uv run ruff check
    uv run ruff format --check

typecheck:
    uv run ty check

typecheck-watch:
    uv run ty check --watch

dev:
    uv run python main.py

test:
    uv run pytest --cov=. --cov-report=term-missing

test-ci:
    uv run pytest

all: check typecheck test

