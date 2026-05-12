# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Install Playwright browsers (required before first run)
uv run playwright install chromium

# Run the scraper (headless by default) — scrapes all 3 languages sequentially
make run
# or: uv run python main.py

# Scrape a single language (en / es / ru)
uv run python main.py --language es

# Run with visible browser (requires Xvfb on headless systems: xvfb-run uv run ...)
uv run python main.py --headed

# Save output to a custom directory
uv run python main.py --output-dir ./data

# Format + lint
make lint
# or: uv run ruff format . && uv run ruff check --fix .
```

Linting is configured via [ruff](https://docs.astral.sh/ruff/) (dev dependency). There are no tests configured yet.

## Architecture

The scraper automates a Chromium browser via Playwright to extract exam questions from `start4drive.com.ar`. The site requires an active browser session (no REST API alternative is known).

**Flow:** `main.py` → (for each language) fresh browser → `browser.initialize_session` (home → accept terms → dashboard → select language → new test → eye toggle for EN/RU) → `pagination.scrape_test` (async generator, yields one question at a time) → `extractor.extract_question` (per-question extraction) → `output.write_progress` (rewrites JSON after each question).

### Module responsibilities

- **`scraper/browser.py`** — launches the browser, navigates from the homepage to an active test URL, and exposes low-level helpers (`wait_for_question`, `click_next`). All CSS selectors are defined here as constants. Language selection happens on the dashboard modal using JS `.click()` (the picker is `<div>` elements blocked by a backdrop overlay, not `<button>`).
- **`scraper/extractor.py`** — extracts a single question. To reveal the correct answer, it clicks the first radio button and hits "Verify" (label varies by language), then reads which `<li>` received the `CORRECT_CLS` class. Text extraction is language-aware: ES UI uses `div.Qe5J54-r` (`innerText`); EN/RU UI reads `h2.FdSXAi7I.innerText` / `div.Qe5J54-r.innerText` after the eye toggle is activated (see `initialize_session`).
- **`scraper/pagination.py`** — async generator that drives the full test loop. Stops on: cycle detection (already-seen `question_id`), missing next button, or DOM not updating after a click.
- **`scraper/output.py`** — rewrites `output/<language>/<test_id>.json` after each question so progress is never lost on crash.

### Output schema

Output is written to `output/<language>/<test_id>.json`:

```json
{
  "meta": { "test_id", "language", "scraped_at", "total_questions", "source_url" },
  "questions": [
    {
      "question_index": 0,
      "question_id": "<radio input name attr>",
      "text": "...",
      "image_url": null,
      "options": [{ "index": 0, "text": "...", "is_correct": false }, ...],
      "correct_option_index": 2,
      "is_multiple_choice": false
    }
  ]
}
```

### Selector fragility

Most CSS selectors (`h2.FdSXAi7I`, `input.Phvp4eQ3`, `button.tWI-IRMI`, `EcflB-k8`) are obfuscated class names shared across all UI languages. Two selectors differ by language:

| Element | ES UI | EN / RU UI |
|---|---|---|
| Question text | `h2.FdSXAi7I` → `div.Qe5J54-r` (`innerText`) | `h2.FdSXAi7I.innerText` (after eye toggle) |
| Option text | `li div.Qe5J54-r` (`innerText`) | same — `innerText` after eye toggle |
| Verify button label | `Verificar` | `Verify` / `Проверить` |
| Eye toggle button | n/a | `.N6cjtZ0-` — clicked once in `initialize_session` |

When selectors stop working, inspect the live DOM with `xvfb-run uv run python main.py --headed` to find the new names.
