from concurrent.futures import ThreadPoolExecutor, as_completed

from src.scrapers.factory import ScraperFactory
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class ScraperOrchestrator:
    def __init__(self, scrapers_config_path):
        self.scrapers_config = ConfigLoader(scrapers_config_path)
        self.scraper_names = ScraperFactory.available_scrapers()

    def _run_scraper(self, name):
        config = self.scrapers_config.get_config(name)
        scraper_cls = ScraperFactory._registry.get(name)
        if not scraper_cls:
            logger.error(f"Scraper '{name}' not registered!")
            return []
        categories = config['categories']
        base_url = config['base_url']
        logger.info(f"Running {name} scraper...")
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
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._run_scraper, name)
                for name in self.scraper_names
            ]
            for future in as_completed(futures):
                try:
                    all_products.extend(future.result())
                except Exception as e:
                    logger.error(f"Scraper failed: {e}")
        return all_products
