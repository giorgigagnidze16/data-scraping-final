import json

from src.data import database
from src.scrapers.selenium_scraper import AmazonSeleniumScraper
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor


def run_amazon(config):
    print("\n==== Amazon Scraper ====")
    amazon_config = config.get_config('amazon')
    categories = amazon_config['categories']
    base_url = amazon_config['base_url']
    return threaded_scrape_executor(
        scraper_cls=AmazonSeleniumScraper,
        base_config=amazon_config,
        jobs=categories,
        max_workers=len(categories),
        url_prefix=base_url,
    )


def run_db(config):
    db_cfg = ConfigLoader(config).get_config("database")

    database.configure_engine(
        host=db_cfg["host"],
        port=db_cfg["port"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        dbname=db_cfg["dbname"]
    )

    database.init_db_with_sql("schema.sql")


def main():
    config = ConfigLoader("config/scrapers.yaml")
    amazon_results = run_amazon(config)
    print("\nAmazon Scraper done. Sample data:")
    for cat, items in amazon_results.items():
        print(f"  {cat}: {items[:2]}")
    with open("amazon_results.json", "w", encoding="utf-8") as f:
        json.dump(amazon_results, f, indent=2, ensure_ascii=False)

    run_db("config/database.yaml")

    all_products = []
    for category, items in amazon_results.items():
        for product in items:
            product['source'] = 'amazon'
            product['category'] = category
            all_products.append(product)

    database.save_products(all_products)
    print(f"\nSaved {len(all_products)} products to the database.")


if __name__ == "__main__":
    main()
