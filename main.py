import argparse
import asyncio

from scraper.browser import launch_browser, initialize_session
from scraper.pagination import scrape_test
from scraper.output import save_results


async def run(output_dir: str, headless: bool) -> None:
    pw, browser, context, page = await launch_browser(headless=headless)
    try:
        test_url = await initialize_session(page)
        test_id = test_url.split("/test/")[1].split("/")[0]
        print(f"Session started: test_id={test_id}")

        questions = await scrape_test(page)
        path = save_results(questions, test_id, output_dir)
        print(f"\nDone. {len(questions)} questions saved to {path}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape start4drive.com.ar exam questions")
    parser.add_argument("--output-dir", default="output", help="Directory for JSON output")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()

    asyncio.run(run(args.output_dir, headless=not args.headed))


if __name__ == "__main__":
    main()
