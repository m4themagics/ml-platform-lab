.PHONY: install lint test check data train

install:
	uv sync --extra dev

lint:
	uv run ruff check .

test:
	uv run pytest

data:
	uv run python -m services.fraud_scoring.data

train:
	uv run python -m services.fraud_scoring.train

check: lint test
