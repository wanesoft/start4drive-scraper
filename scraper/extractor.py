import asyncio
from playwright.async_api import Page
from .browser import QUESTION_SELECTOR, RADIO_SELECTOR, CORRECT_CLS


async def extract_question(page: Page, question_index: int) -> dict | None:
    if not await page.query_selector(QUESTION_SELECTOR):
        return None

    question_id = await _get_question_id(page)
    text = await _get_question_text(page)
    image_url = await _get_image_url(page, question_id)
    options, correct_index = await _get_options_with_correct(page)

    return {
        "question_index": question_index,
        "question_id": question_id,
        "text": text,
        "image_url": image_url,
        "options": options,
        "correct_option_index": correct_index,
        "is_multiple_choice": len([o for o in options if o["is_correct"]]) > 1,
    }


async def _get_question_id(page: Page) -> str | None:
    el = await page.query_selector(RADIO_SELECTOR)
    if el:
        return await el.get_attribute("name")
    return None


async def _get_question_text(page: Page) -> str:
    parts = await page.eval_on_selector_all(
        f"{QUESTION_SELECTOR} span.qDW3uMC9",
        "els => els.map(e => e.innerText.trim())",
    )
    return " ".join(p for p in parts if p)


async def _get_image_url(page: Page, question_id: str | None) -> str | None:
    img = await page.query_selector("._0iYwjiDt img")
    if img:
        src = await img.get_attribute("src")
        return src
    return None


async def _get_options_with_correct(page: Page) -> tuple[list[dict], int | None]:
    # Read option texts before answering
    raw = await page.eval_on_selector_all(
        "li",
        "els => els.map(e => { const s = e.querySelector('span.qDW3uMC9'); return s ? s.innerText.trim() : null; })",
    )
    option_texts = [t for t in raw if t]

    if not option_texts:
        return [], None

    # Select first radio and click Verify to reveal correct answer
    await page.evaluate("document.querySelector('input.Phvp4eQ3').click()")
    await asyncio.sleep(0.2)
    await page.evaluate(
        "([...document.querySelectorAll('button')]"
        ".find(b => b.innerText.includes('Verify')) || {}).click?.()"
    )
    await asyncio.sleep(0.8)

    # Read LI classes after verification
    li_classes = await page.eval_on_selector_all(
        "li",
        "els => els.filter(e => e.querySelector('span.qDW3uMC9')).map(e => e.className)",
    )

    correct_index = None
    options = []
    for i, (text, cls) in enumerate(zip(option_texts, li_classes)):
        is_correct = CORRECT_CLS in cls
        if is_correct:
            correct_index = i
        options.append({"index": i, "text": text, "is_correct": is_correct})

    return options, correct_index
