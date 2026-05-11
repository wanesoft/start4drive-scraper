import asyncio
from playwright.async_api import Page
from .browser import wait_for_question, click_next, QUESTION_SELECTOR
from .extractor import extract_question

MAX_QUESTIONS = 1000


async def scrape_test(page: Page) -> list[dict]:
    questions: list[dict] = []
    seen_ids: set[str] = set()

    for index in range(MAX_QUESTIONS):
        found = await wait_for_question(page, timeout=10_000)
        if not found:
            print(f"[stop] Question element not found at index {index}")
            break

        data = await extract_question(page, index)
        if data is None:
            print(f"[stop] Extraction returned None at index {index}")
            break

        qid = data.get("question_id")

        # Stop if we've looped back to an already-seen question
        if qid and qid in seen_ids:
            print(f"[stop] Cycle detected at index {index} (question_id={qid} already seen)")
            break
        if qid:
            seen_ids.add(qid)

        questions.append(data)
        text_preview = data["text"][:70]
        print(f"[{index:03d}] {qid}: {text_preview}...")

        # Navigate to next question
        has_next = await click_next(page)
        if not has_next:
            print(f"[stop] No next button at index {index} — reached last question")
            break

        await asyncio.sleep(0.3)

        # Wait for DOM to update to the next question
        try:
            await page.wait_for_function(
                f"document.querySelector('input[name]')?.name !== '{qid}'",
                timeout=8_000,
            )
        except Exception:
            print(f"[warn] DOM did not update after index {index}")
            break

    return questions
