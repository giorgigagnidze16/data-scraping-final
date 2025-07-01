from concurrent.futures import ProcessPoolExecutor, as_completed

from src.scrapers.factory import ScraperFactory
from src.utils.config import ConfigLoader
from src.utils.executor import threaded_scrape_executor
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class ScraperOrchestrator:
    """
    Orchestrates the execution of all registered product scrapers,
    manages their configurations, and aggregates all product results.
    Handles both threaded and Scrapy-based scrapers in a parallelized workflow.

    Args:
        scrapers_config_path (str): Path to the YAML configuration file for scrapers.

    Attributes:
        scrapers_config (ConfigLoader): Loader for all scraper configs.
        scraper_names (list of str): All available scrapers registered in the factory.
    """

    def __init__(self, scrapers_config_path):
        self.scrapers_config = ConfigLoader(scrapers_config_path)
        self.scraper_names = ScraperFactory.available_scrapers()
        logger.info(f"Available scrapers '{self.scraper_names}'")

    def _run_scraper(self, name):
        """
        Runs a single scraper by name using its configuration.

        Args:
            name (str): Name/ID of the scraper to run.

        Returns:
            list: List of product dicts scraped by this scraper.

        Notes:
            - For Scrapy-based scrapers (is_scrapy = True), scraping runs in the main process.
            - For other scrapers, scraping is parallelized using threads per category.
            - All products are annotated with their 'source' and 'category'.
            - Any exceptions are caught and logged; returns empty list on error.
        """
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
        """
        Runs all configured scrapers in parallel using process pool.

        Args:
            max_workers (int): Maximum number of processes (scrapers run in parallel).
                               Default is 2.

        Returns:
            list: Combined list of all products from all scrapers.

        Notes:
            - Each scraper runs in a separate process for isolation.
            - Aggregates all results into a single product list.
            - Scraper failures are logged and do not interrupt the rest.
        """
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
