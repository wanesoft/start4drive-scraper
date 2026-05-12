import asyncio
from playwright.async_api import Page
from .browser import QUESTION_SELECTOR, RADIO_SELECTOR, CORRECT_CLS

_ES_TEXT_SEL = "div.Qe5J54-r"
_VERIFY_LABELS = ["Verify", "Verificar", "Проверить"]


async def extract_question(
    page: Page, question_index: int, language: str = "es"
) -> dict | None:
    if not await page.query_selector(QUESTION_SELECTOR):
        return None

    question_id = await _get_question_id(page)
    text = await _get_question_text(page, language)
    image_url = await _get_image_url(page, question_id)
    options, correct_index = await _get_options_with_correct(page, language)

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


async def _get_question_text(page: Page, language: str) -> str:
    if language == "es":
        parts = await page.eval_on_selector_all(
            f"{QUESTION_SELECTOR} {_ES_TEXT_SEL}",
            "els => els.map(e => e.innerText.trim())",
        )
        return " ".join(p for p in parts if p)
    else:
        # After the eye toggle, h2.innerText yields the full translated sentence directly.
        return await page.eval_on_selector(
            QUESTION_SELECTOR, "el => el.innerText.trim()"
        )


async def _get_image_url(page: Page, question_id: str | None) -> str | None:
    img = await page.query_selector("._0iYwjiDt img")
    if img:
        src = await img.get_attribute("src")
        return src
    return None


async def _get_options_with_correct(
    page: Page, language: str
) -> tuple[list[dict], int | None]:
    # After the eye toggle (EN/RU) or in ES mode, div.Qe5J54-r.innerText gives the
    # visible option text in the active language.
    raw = await page.eval_on_selector_all(
        "li",
        f"els => els.map(e => {{ const s = e.querySelector('{_ES_TEXT_SEL}'); return s ? s.innerText.trim() : null; }})",
    )
    option_texts = [t for t in raw if t]

    if not option_texts:
        return [], None

    await page.evaluate("document.querySelector('input.Phvp4eQ3').click()")
    await asyncio.sleep(0.2)
    await page.evaluate(
        f"([...document.querySelectorAll('button')]"
        f".find(b => {_VERIFY_LABELS!r}.some(t => b.innerText.includes(t))) || {{}}).click?.()"
    )
    await asyncio.sleep(0.8)

    li_classes = await page.eval_on_selector_all(
        "li",
        f"els => els.filter(e => e.querySelector('{_ES_TEXT_SEL}')).map(e => e.className)",
    )

    correct_index = None
    options = []
    for i, (text, cls) in enumerate(zip(option_texts, li_classes)):
        is_correct = CORRECT_CLS in cls
        if is_correct:
            correct_index = i
        options.append({"index": i, "text": text, "is_correct": is_correct})

    return options, correct_index
