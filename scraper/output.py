import json
import os


def write_progress(
    questions: list[dict], test_id: str, scraped_at: str, output_dir: str
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{test_id}.json")

    payload = {
        "meta": {
            "test_id": test_id,
            "scraped_at": scraped_at,
            "total_questions": len(questions),
            "source_url": f"https://www.start4drive.com.ar/test/{test_id}/ordered/0",
        },
        "questions": questions,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path
