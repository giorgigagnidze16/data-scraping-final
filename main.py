import json

from src.scrapers.selenium_scraper import AmazonSeleniumScraper
from src.utils.config import ConfigLoader


def run_amazon(config):
    print("\n==== Amazon Scraper ====")
    amazon_config = config.get_site_config('amazon')
    amazon_scraper = AmazonSeleniumScraper(amazon_config)
    results = {}
    for cat, path in amazon_config['categories'].items():
        print(f"Scraping Amazon category: {cat}")
        url = amazon_config['base_url'] + path
        try:
            items = amazon_scraper.scrape_category(url)
            print(f"  Found {len(items)} products.")
            results[cat] = items
        except Exception as e:
            print(f"  ERROR: {e}")
            results[cat] = []
    return results


def main():
    config = ConfigLoader("config/scrapers.yaml")

    amazon_results = run_amazon(config)
    print(f"\nAmazon Scraper done. Sample data:")
    for cat, items in amazon_results.items():
        print(f"  {cat}: {items[:2]}")

    with open("amazon_results.json", "w", encoding="utf-8") as f:
        json.dump(amazon_results, f, indent=2, ensure_ascii=False)



if __name__ == "__main__":
    main()
