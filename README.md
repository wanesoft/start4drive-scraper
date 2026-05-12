# start4drive-scraper

Scraper for [start4drive.com.ar](https://www.start4drive.ar) — extracts all exam questions with correct answers in English, Spanish, and Russian.

The site has no public API; the scraper automates a headless Chromium browser via [Playwright](https://playwright.dev/).

## Output

Questions are saved to `output/<language>/<test_id>.json` after each question, so a crash loses at most one question.

```
output/
  en/  <test_id>.json   ← English translations
  es/  <test_id>.json   ← Spanish (original)
  ru/  <test_id>.json   ← Russian translations
```

Each file:

```json
{
  "meta": {
    "test_id": "abc123",
    "language": "en",
    "scraped_at": "2026-05-11T17:00:00+00:00",
    "total_questions": 458,
    "source_url": "https://www.start4drive.com.ar/test/abc123/ordered/0"
  },
  "questions": [
    {
      "question_index": 0,
      "question_id": "b-001",
      "text": "According to the World Health Organization...",
      "image_url": "/assets/001-abc.webp",
      "options": [
        { "index": 0, "text": "True",  "is_correct": true  },
        { "index": 1, "text": "False", "is_correct": false }
      ],
      "correct_option_index": 0,
      "is_multiple_choice": false
    }
  ]
}
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
uv run playwright install chromium
```

## Usage

```bash
# Scrape all languages (en, es, ru) — default
make run
# or
uv run python main.py

# Single language
uv run python main.py --language en
uv run python main.py --language es
uv run python main.py --language ru

# Custom output directory
uv run python main.py --output-dir ./data

# Visible browser (useful for debugging broken selectors)
# On headless systems (WSL, CI) wrap with xvfb-run:
xvfb-run uv run python main.py --headed
```

## How it works

1. **Accept terms** — clicks "Ok, let's go!" on the home page.
2. **Select language** — clicks the language picker on the dashboard modal (the buttons are `<div>` elements under a backdrop, so clicks go through JS, not Playwright coordinates).
3. **Start test** — clicks "New test" / "Nuevo test" / "Новый тест".
4. **Enable translations** (EN/RU only) — clicks the eye-icon button (`.N6cjtZ0-`) in the header once. This toggles the page from per-word Spanish display into full-sentence translation mode, after which `h2.innerText` yields the complete translated question.
5. **Scrape loop** — for each question: extracts text and options, clicks the first radio button, clicks "Verify" to reveal the correct answer, advances to the next question.
6. **Stop conditions** — cycle detection (duplicate `question_id`), missing next button, DOM not updating.

### Translation mechanics

The site shows questions in Spanish by default. In EN/RU mode each word is wrapped in a `span.LGdSgx4z` that holds the Spanish text (`span.qDW3uMC9`, visible) and a per-word translation tooltip (`span.vK65g4nl`, CSS-hidden, appears on hover).

A header button with an eye icon (`.N6cjtZ0-`) toggles "translation mode": clicking it replaces the Spanish words with the full translated sentence so that `h2.innerText` returns the complete, fluent translation. The scraper clicks this button once per session for EN/RU languages.

```html
<!-- EN / RU UI (after eye toggle — h2.innerText gives translated sentence) -->
<span class="LGdSgx4z">
  <span class="qDW3uMC9">Verdadero</span>   <!-- Spanish -->
  <span class="vK65g4nl">True</span>         <!-- translation (now visible) -->
</span>

<!-- ES UI -->
<div class="Qe5J54-r">Verdadero</div>
```

## Selector fragility

Most CSS selectors (`h2.FdSXAi7I`, `input.Phvp4eQ3`, `button.tWI-IRMI`, `EcflB-k8`) are obfuscated class names. They break if the site redeploys. To find new names, run with `--headed` and inspect the DOM.

Key selectors that differ by language:

| Element | ES UI | EN / RU UI |
|---|---|---|
| Question text | `h2 div.Qe5J54-r` (`innerText`) | `h2.innerText` (after eye toggle) |
| Option text | `li div.Qe5J54-r` (`innerText`) | same — `innerText` after eye toggle |
| Verify button | `Verificar` | `Verify` / `Проверить` |
| Eye toggle | n/a | `.N6cjtZ0-` (clicked once on session start) |

## Development

```bash
make lint   # ruff format + ruff check --fix
```
