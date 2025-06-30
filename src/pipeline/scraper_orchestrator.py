from concurrent.futures import ProcessPoolExecutor, as_completed

from src.scrapers.factory import ScraperFactory
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class ScraperOrchestrator:
    def __init__(self, scrapers_config_path):
        self.scrapers_config = ConfigLoader(scrapers_config_path)
        self.scraper_names = ScraperFactory.available_scrapers()
        logger.info(f"Available scrapers '{self.scraper_names}'")

    def _run_scraper(self, name):
        config = self.scrapers_config.get_config(name)
        scraper_cls = ScraperFactory._registry.get(name)
        if not scraper_cls:
            logger.error(f"Scraper '{name}' not registered!")
            return []
        categories = config['categories']
        base_url = config['base_url']
        logger.info(f"Running {name} scraper...")

        if getattr(scraper_cls, "is_scrapy", False):
            urls = [base_url + v for v in categories.values()]
            logger.info(f"[ALL CATEGORIES] Scraping {urls} with Scrapy (main thread)...")
            try:
                items = scraper_cls(config).scrape(urls)
                for prod in items:
                    prod['source'] = name
                    if 'category' not in prod or not prod['category']:
                        prod['category'] = next((k for k, v in categories.items() if v in (prod.get('url') or '')),
                                                None)
                logger.info(f"{name} Scrapy scraper finished with {len(items)} products.")
                return items
            except Exception as e:
                logger.error(f"Scrapy scraper '{name}' failed: {e}", exc_info=True)
                return []

        results = threaded_scrape_executor(
            scraper_cls=scraper_cls,
            base_config=config,
            jobs=categories,
            max_workers=len(categories) + 2,
            url_prefix=base_url,
        )
        all_products = []
        for category, items in results.items():
            for product in items:
                product['source'] = name
                product['category'] = category
                all_products.append(product)
        logger.info(f"{name} scraper finished with {sum(len(v) for v in results.values())} products.")
        return all_products

    def run_all(self, max_workers=2):
        all_products = []
        scraper_futures = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for name in self.scraper_names:
                scraper_futures.append(
                    executor.submit(self._run_scraper, name)
                )
            for future in as_completed(scraper_futures):
                try:
                    all_products.extend(future.result())
                except Exception as e:
                    logger.error(f"Scraper failed: {e}")
        return all_products
