from playwright.async_api import async_playwright, Page

BASE_URL = "https://www.start4drive.com.ar"

QUESTION_SELECTOR = "h2.FdSXAi7I"
OPTION_SELECTOR = "li"
RADIO_SELECTOR = "input.Phvp4eQ3"
NEXT_BTN_SELECTOR = "button.tWI-IRMI"
CORRECT_CLS = "EcflB-k8"
EYE_TOGGLE_SELECTOR = ".N6cjtZ0-"


async def launch_browser(headless: bool = True):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    page = await context.new_page()
    return pw, browser, context, page


async def _js_click_by_text(page: Page, text: str) -> bool:
    """Click the first leaf element whose innerText exactly matches `text` via JS."""
    return await page.evaluate(
        f"""(() => {{
            const el = [...document.querySelectorAll('*')]
                .find(e => e.children.length === 0 && e.innerText?.trim() === '{text}');
            if (el) {{ el.click(); return true; }}
            return false;
        }})()"""
    )


_LANG_LABEL: dict[str, str] = {
    "en": "En",
    "es": "Es",
    "ru": "Ру",  # Cyrillic — shown as "Ру" in the dashboard language picker
}

_NEW_TEST_LABELS = [
    "New test",
    "Nuevo test",
    "Nuevo examen",
    "Новый тест",
    "Новий тест",
]


async def initialize_session(page: Page, language: str = "es") -> str:
    await page.goto(BASE_URL + "/", wait_until="networkidle", timeout=30_000)

    # Step 1: accept terms ("Ok, let's go!" is the only <button> on the home page)
    await page.evaluate(
        "([...document.querySelectorAll('button')]"
        '.find(b => b.innerText.includes("let\'s go")) || {}).click?.()'
    )
    await page.wait_for_url("**/dashboard", timeout=10_000)

    # Step 2: select language in the dashboard modal.
    # The picker uses <div> elements (not <button>), blocked by a backdrop overlay,
    # so we bypass with a direct JS .click() on the matching leaf node.
    lang_label = _LANG_LABEL.get(language, language.capitalize())
    await _js_click_by_text(page, lang_label)

    # Language selection re-renders the dashboard; wait until buttons reappear
    await page.wait_for_function(
        "document.querySelectorAll('button').length > 0", timeout=15_000
    )

    # Step 3: click "New test" (label varies by language)
    await page.evaluate(
        f"([...document.querySelectorAll('button')]"
        f".find(b => {_NEW_TEST_LABELS!r}.some(t => b.innerText.includes(t)))"
        f" || {{}}).click?.()"
    )
    await page.wait_for_url("**/test/**", timeout=15_000)
    await page.wait_for_selector(QUESTION_SELECTOR, timeout=15_000)

    # For EN/RU: enable full-sentence translation mode via the eye toggle in the header.
    # The toggle replaces per-word Spanish with the translated sentence in h2.innerText.
    if language != "es":
        await page.evaluate(
            f"(document.querySelector('{EYE_TOGGLE_SELECTOR}') || {{}}).click?.()"
        )
        await page.wait_for_timeout(300)

    return page.url


async def wait_for_question(page: Page, timeout: int = 10_000) -> bool:
    try:
        await page.wait_for_selector(QUESTION_SELECTOR, timeout=timeout)
        return True
    except Exception:
        return False


async def click_next(page: Page) -> bool:
    btn = await page.query_selector(NEXT_BTN_SELECTOR)
    if not btn:
        return False
    disabled = await btn.get_attribute("disabled")
    if disabled is not None:
        return False
    await page.evaluate(f"document.querySelector('{NEXT_BTN_SELECTOR}').click()")
    return True
