from src.utils.logger import get_logger
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor

from src.scrapers.selenium_scraper import AmazonSeleniumScraper
# from src.scrapers.ebay_scraper import EbayScraper
# from src.scrapers.etsy_scraper import EtsyScraper

logger = get_logger("orchestrator")

class ScraperOrchestrator:
    def __init__(self, scrapers_config_path):
        self.scrapers_config = ConfigLoader(scrapers_config_path)
        self.scraper_classes = {
            "amazon": AmazonSeleniumScraper,
        }

    def run_all(self):
        all_products = []
        for name, scraper_cls in self.scraper_classes.items():
            config = self.scrapers_config.get_config(name)
            categories = config['categories']
            base_url = config['base_url']
            logger.info(f"Running {name} scraper...")
            results = threaded_scrape_executor(
                scraper_cls=scraper_cls,
                base_config=config,
                jobs=categories,
                max_workers=len(categories),
                url_prefix=base_url,
            )
            for category, items in results.items():
                for product in items:
                    product['source'] = name
                    product['category'] = category
                    all_products.append(product)
            logger.info(f"{name} scraper finished with {sum(len(v) for v in results.values())} products.")
        return all_products
