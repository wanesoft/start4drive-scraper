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
4. **Scrape loop** — for each question: extracts text and options, clicks the first radio button, clicks "Verify" to reveal the correct answer, advances to the next question.
5. **Stop conditions** — cycle detection (duplicate `question_id`), missing next button, DOM not updating.

### Translation mechanics

The site serves per-word translations alongside the original Spanish:

```html
<!-- EN / RU UI -->
<span class="LGdSgx4z">
  <span class="qDW3uMC9">Verdadero</span>   <!-- Spanish, visible -->
  <span class="vK65g4nl">True</span>         <!-- translation, CSS-hidden -->
</span>

<!-- ES UI -->
<div class="Qe5J54-r">Verdadero</div>
```

Translations are extracted via `textContent` (not `innerText`) to bypass CSS visibility hiding.

## Selector fragility

Most CSS selectors (`h2.FdSXAi7I`, `input.Phvp4eQ3`, `button.tWI-IRMI`, `EcflB-k8`) are obfuscated class names. They break if the site redeploys. To find new names, run with `--headed` and inspect the DOM.

Two selectors differ by UI language:

| Element | ES UI | EN / RU UI |
|---|---|---|
| Question / option text | `div.Qe5J54-r` (`innerText`) | `span.vK65g4nl` (`textContent`) |
| Verify button | `Verificar` | `Verify` / `Проверить` |

## Development

```bash
make lint   # ruff format + ruff check --fix
```
