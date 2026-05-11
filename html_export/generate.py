"""Generate a self-contained HTML file from scraped question JSON files."""

import argparse
import json
import urllib.request
from html import escape
from pathlib import Path

BASE_URL = "https://www.start4drive.com.ar"
LANG_LABELS = {"en": "EN", "es": "ES", "ru": "RU"}
OPTION_LETTERS = "ABCDEFGH"


def load_data(output_dir: Path) -> dict[str, list[dict]]:
    """Return {lang: [question, ...]} for every JSON file found."""
    result: dict[str, list[dict]] = {}
    for json_path in sorted(output_dir.glob("*/*.json")):
        lang = json_path.parent.name
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
        result.setdefault(lang, []).extend(data["questions"])
        result.setdefault(f"_meta_{lang}", data["meta"])  # type: ignore[arg-type]
    return result


def build_image_map(data: dict) -> dict[str, str]:
    """Return {question_id: image_url} merging all languages; base64 takes priority."""
    image_map: dict[str, str] = {}
    for key, questions in data.items():
        if key.startswith("_meta_") or not isinstance(questions, list):
            continue
        for q in questions:
            qid = q["question_id"]
            url = q.get("image_url")
            if not url:
                continue
            existing = image_map.get(qid)
            if existing is None or (
                not existing.startswith("data:") and url.startswith("data:")
            ):
                image_map[qid] = url
    return image_map


def download_images(image_map: dict[str, str], assets_dir: Path) -> None:
    """Download path-based images to assets_dir; update image_map in place to local paths."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    path_entries = [
        (qid, url) for qid, url in image_map.items() if not url.startswith("data:")
    ]
    total = len(path_entries)
    for i, (qid, url) in enumerate(path_entries, 1):
        filename = Path(url).name
        local_path = assets_dir / filename
        if not local_path.exists():
            print(f"[{i}/{total}] downloading {filename}")
            urllib.request.urlretrieve(BASE_URL + url, local_path)
        else:
            print(f"[{i}/{total}] skip {filename} (exists)")
        image_map[qid] = f"assets/{filename}"


def render_question(q: dict, image_map: dict[str, str]) -> str:
    qid = q["question_id"]
    idx = q["question_index"] + 1
    text = escape(q["text"])
    img_url = image_map.get(qid)

    img_html = ""
    if img_url:
        img_html = f'<img src="{escape(img_url)}" alt="question image" class="q-img">'

    options_html = ""
    for opt in q["options"]:
        letter = OPTION_LETTERS[opt["index"]]
        opt_text = escape(opt["text"])
        cls = ' class="correct"' if opt["is_correct"] else ""
        options_html += f"<li{cls}><strong>{letter}.</strong> {opt_text}</li>\n"

    return f"""<div class="question">
  <div class="q-header">
    <span class="q-num">{idx}</span>
    <span class="q-id">{escape(qid)}</span>
  </div>
  <p class="q-text">{text}</p>
  {img_html}
  <ul class="options">{options_html}</ul>
</div>"""


def render_html(data: dict, image_map: dict[str, str]) -> str:
    langs = [k for k in data if not k.startswith("_meta_")]
    langs_sorted = sorted(
        langs,
        key=lambda lang: list(LANG_LABELS).index(lang) if lang in LANG_LABELS else 99,
    )

    tabs_html = ""
    panels_html = ""

    for i, lang in enumerate(langs_sorted):
        label = LANG_LABELS.get(lang, lang.upper())
        active_tab = " active" if i == 0 else ""
        active_panel = " active" if i == 0 else ""
        meta = data.get(f"_meta_{lang}", {})

        questions = data[lang]
        questions_html = "\n".join(render_question(q, image_map) for q in questions)

        tabs_html += (
            f'<button class="tab{active_tab}" data-lang="{lang}">{label}</button>\n'
        )
        panels_html += f"""<div class="panel{active_panel}" id="panel-{lang}">
  <div class="meta">
    Test ID: <strong>{escape(str(meta.get("test_id", "")))}</strong> &nbsp;|&nbsp;
    Questions: <strong>{len(questions)}</strong> &nbsp;|&nbsp;
    Scraped: <strong>{escape(str(meta.get("scraped_at", ""))[:10])}</strong>
  </div>
  {questions_html}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Start4Drive — Questions</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #f5f5f5; color: #222; }}
  h1 {{ text-align: center; padding: 1.5rem 1rem 0.5rem; margin: 0; font-size: 1.4rem; }}
  .tabs {{ display: flex; justify-content: center; gap: 0.5rem; padding: 0.75rem; background: #fff; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 10; }}
  .tab {{ padding: 0.4rem 1.4rem; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.95rem; transition: background 0.15s; }}
  .tab:hover {{ background: #f0f0f0; }}
  .tab.active {{ background: #2563eb; color: #fff; border-color: #2563eb; }}
  .panel {{ display: none; max-width: 860px; margin: 0 auto; padding: 1rem; }}
  .panel.active {{ display: block; }}
  .meta {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 0.6rem 1rem; margin-bottom: 1.2rem; font-size: 0.88rem; color: #555; }}
  .question {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem; }}
  .q-header {{ display: flex; align-items: baseline; gap: 0.6rem; margin-bottom: 0.5rem; }}
  .q-num {{ font-size: 1.1rem; font-weight: 700; color: #2563eb; min-width: 2rem; }}
  .q-id {{ font-size: 0.75rem; color: #999; }}
  .q-text {{ margin: 0 0 0.75rem; line-height: 1.5; }}
  .q-img {{ display: block; max-width: 100%; max-height: 260px; margin-bottom: 0.75rem; border-radius: 4px; }}
  .options {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.35rem; }}
  .options li {{ padding: 0.35rem 0.75rem; border-radius: 4px; border: 1px solid #e8e8e8; font-size: 0.95rem; }}
  .options li.correct {{ background: #d1fae5; border-color: #6ee7b7; font-weight: 600; color: #065f46; }}
</style>
</head>
<body>
<h1>Start4Drive — Exam Questions</h1>
<div class="tabs">
{tabs_html}</div>
{panels_html}
<script>
  document.querySelectorAll('.tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('panel-' + btn.dataset.lang).classList.add('active');
    }});
  }});
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate HTML from scraped question JSON files."
    )
    parser.add_argument(
        "--output-dir", default="output", help="Directory with language subdirs"
    )
    parser.add_argument(
        "--html-out",
        default=None,
        help="Output HTML path (default: <output-dir>/index.html)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    html_out = Path(args.html_out) if args.html_out else output_dir / "index.html"
    assets_dir = output_dir / "assets"

    print("Loading JSON data...")
    data = load_data(output_dir)
    langs = [k for k in data if not k.startswith("_meta_")]
    print(f"Found languages: {langs}")

    print("Building image map...")
    image_map = build_image_map(data)

    print("Downloading images...")
    download_images(image_map, assets_dir)

    print("Generating HTML...")
    html = render_html(data, image_map)
    html_out.write_text(html, encoding="utf-8")
    print(f"Done → {html_out}")


if __name__ == "__main__":
    main()
