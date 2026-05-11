import argparse
import asyncio
from datetime import datetime, timezone

from scraper.browser import launch_browser, initialize_session
from scraper.pagination import scrape_test
from scraper.output import write_progress


async def run(output_dir: str, headless: bool) -> None:
    pw, browser, context, page = await launch_browser(headless=headless)
    try:
        test_url = await initialize_session(page)
        test_id = test_url.split("/test/")[1].split("/")[0]
        print(f"Session started: test_id={test_id}")

        scraped_at = datetime.now(timezone.utc).isoformat()
        questions: list[dict] = []
        path = ""

        async for question in scrape_test(page):
            questions.append(question)
            path = write_progress(questions, test_id, scraped_at, output_dir)

        print(f"\nDone. {len(questions)} questions saved to {path}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()


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
    args = parser.parse_args()

    asyncio.run(run(args.output_dir, headless=not args.headed))


if __name__ == "__main__":
    main()
