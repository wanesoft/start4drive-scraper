import json
import os
from datetime import datetime, timezone


def save_results(questions: list[dict], test_id: str, output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{test_id}.json")

    payload = {
        "meta": {
            "test_id": test_id,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_questions": len(questions),
            "source_url": f"https://www.start4drive.com.ar/test/{test_id}/ordered/0",
        },
        "questions": questions,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path
