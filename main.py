import argparse
import asyncio
from datetime import datetime, timezone

from scraper.browser import launch_browser, initialize_session
from scraper.pagination import scrape_test
from scraper.output import write_progress


LANGUAGES = ["en", "es", "ru"]


async def run_language(output_dir: str, headless: bool, language: str) -> None:
    pw, browser, context, page = await launch_browser(headless=headless)
    try:
        test_url = await initialize_session(page, language=language)
        test_id = test_url.split("/test/")[1].split("/")[0]
        print(f"[{language}] Session started: test_id={test_id}")

        scraped_at = datetime.now(timezone.utc).isoformat()
        questions: list[dict] = []
        path = ""

        async for question in scrape_test(page, language=language):
            questions.append(question)
            path = write_progress(questions, test_id, scraped_at, output_dir, language)

        print(f"[{language}] Done. {len(questions)} questions saved to {path}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()


async def run(output_dir: str, headless: bool, languages: list[str]) -> None:
    for language in languages:
        await run_language(output_dir, headless, language)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape start4drive.com.ar exam questions"
    )
    parser.add_argument(
        "--output-dir", default="output", help="Directory for JSON output"
    )
    parser.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode"
    )
    parser.add_argument(
        "--language",
        choices=LANGUAGES + ["all"],
        default="all",
        help="Language to scrape (default: all)",
    )
    args = parser.parse_args()

    languages = LANGUAGES if args.language == "all" else [args.language]
    asyncio.run(run(args.output_dir, headless=not args.headed, languages=languages))


if __name__ == "__main__":
    main()
