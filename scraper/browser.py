from playwright.async_api import async_playwright, Page

BASE_URL = "https://www.start4drive.com.ar"

QUESTION_SELECTOR = "h2.FdSXAi7I"
OPTION_SELECTOR = "li"
RADIO_SELECTOR = "input.Phvp4eQ3"
NEXT_BTN_SELECTOR = "button.tWI-IRMI"
CORRECT_CLS = "EcflB-k8"


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


async def initialize_session(page: Page) -> str:
    """Navigate home → dashboard → start new test. Returns test URL."""
    await page.goto(BASE_URL + "/", wait_until="networkidle", timeout=30_000)
    # Dismiss welcome screen
    await page.evaluate("document.querySelector('button').click()")
    await page.wait_for_url("**/dashboard", timeout=10_000)
    # Start new test
    await page.evaluate(
        "([...document.querySelectorAll('button')]"
        ".find(b => b.innerText.includes('New test')) || {}).click?.()"
    )
    await page.wait_for_url("**/test/**", timeout=15_000)
    await page.wait_for_selector(QUESTION_SELECTOR, timeout=15_000)
    return page.url


async def wait_for_question(page: Page, timeout: int = 10_000) -> bool:
    try:
        await page.wait_for_selector(QUESTION_SELECTOR, timeout=timeout)
        return True
    except Exception:
        return False


async def click_next(page: Page) -> bool:
    """Click the next-question arrow. Returns False if button absent/disabled."""
    btn = await page.query_selector(NEXT_BTN_SELECTOR)
    if not btn:
        return False
    disabled = await btn.get_attribute("disabled")
    if disabled is not None:
        return False
    await page.evaluate(f"document.querySelector('{NEXT_BTN_SELECTOR}').click()")
    return True
