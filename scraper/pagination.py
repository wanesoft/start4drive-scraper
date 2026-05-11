import asyncio
from collections.abc import AsyncGenerator
from playwright.async_api import Page
from .browser import wait_for_question, click_next
from .extractor import extract_question

MAX_QUESTIONS = 1000


async def scrape_test(page: Page) -> AsyncGenerator[dict, None]:
    seen_ids: set[str] = set()

    for index in range(MAX_QUESTIONS):
        found = await wait_for_question(page, timeout=10_000)
        if not found:
            print(f"[stop] Question element not found at index {index}")
            return

        data = await extract_question(page, index)
        if data is None:
            print(f"[stop] Extraction returned None at index {index}")
            return

        qid = data.get("question_id")

        if qid and qid in seen_ids:
            print(
                f"[stop] Cycle detected at index {index} (question_id={qid} already seen)"
            )
            return
        if qid:
            seen_ids.add(qid)

        text_preview = data["text"][:70]
        print(f"[{index:03d}] {qid}: {text_preview}...")
        yield data

        has_next = await click_next(page)
        if not has_next:
            print(f"[stop] No next button at index {index} — reached last question")
            return

        await asyncio.sleep(0.3)

        try:
            await page.wait_for_function(
                f"document.querySelector('input[name]')?.name !== '{qid}'",
                timeout=8_000,
            )
        except Exception:
            print(f"[warn] DOM did not update after index {index}")
            return
