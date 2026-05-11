.PHONY: install run lint clean

install:
	uv sync
	uv run playwright install chromium

run:
	uv run python main.py

lint:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf output/ .venv/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
