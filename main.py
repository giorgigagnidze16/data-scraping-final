import json

from src.scrapers.selenium_scraper import AmazonSeleniumScraper
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor


def run_amazon(config):
    print("\n==== Amazon Scraper ====")
    amazon_config = config.get_site_config('amazon')
    categories = amazon_config['categories']
    base_url = amazon_config['base_url']
    return threaded_scrape_executor(
        scraper_cls=AmazonSeleniumScraper,
        base_config=amazon_config,
        jobs=categories,
        max_workers=len(categories),
        url_prefix=base_url,
    )


def main():
    config = ConfigLoader("config/scrapers.yaml")
    amazon_results = run_amazon(config)
    print("\nAmazon Scraper done. Sample data:")
    for cat, items in amazon_results.items():
        print(f"  {cat}: {items[:2]}")
    with open("amazon_results.json", "w", encoding="utf-8") as f:
        json.dump(amazon_results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
