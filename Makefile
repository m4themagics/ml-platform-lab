.PHONY: install lint test check

install:
	uv sync --extra dev

lint:
	uv run ruff check .

test:
	uv run pytest

check: lint test
