from datetime import datetime

import pandas as pd

from src.analysis.analysis_engine import AnalysisEngine
from src.pipeline.data_pipeline import DataPipeline
from src.pipeline.scraper_orchestrator import ScraperOrchestrator
from src.utils.logger import get_logger

# ======================================================================
# ===============<<<<<>>>>> (MUST INCLUDE) <<<<<>>>>>===================
from src.scrapers.selenium.amazon_scraper import AmazonSeleniumScraper
from src.scrapers.selenium.ebay_selenium_scraper import EbaySeleniumScraper
from src.scrapers.static_scraper import MicroCenterStaticScraper
from src.scrapers.scrapy_crawler.newegg_crawler.spriders.newegg_scrapy import NeweggScrapyScraper
# ===============<<<<<>>>>> (MUST INCLUDE) <<<<<>>>>>===================
# ======================================================================

logger = get_logger("main")


def main():
    try:
        logger.info("Starting pipeline orchestrator...")
        orchestrator = ScraperOrchestrator(scrapers_config_path="config/scrapers.yaml")
        all_products = orchestrator.run_all(4)
        logger.info(f"Scraping complete. {len(all_products)} products collected.")
        if not all_products:
            logger.error("No products scraped! Check your scrapers.")
            return

        logger.info("Running data pipeline...")
        pipeline = DataPipeline(db_config_path="config/database.yaml")
        df_clean = pipeline.run_pipeline(all_products)

        logger.info(f"Cleaned DataFrame shape: {df_clean.shape}")
        if df_clean.empty:
            logger.error("Cleaned DataFrame is empty! Check data cleaning/processing.")
            print(df_clean)
            return

        logger.info("Exporting cleaned product data in all formats...")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        pd.DataFrame(df_clean).to_csv(f"data_output/raw/{timestamp}-products_clean.csv", index=False)
        pd.DataFrame(df_clean).to_json(f"data_output/raw/{timestamp}-products_clean.json", orient="records",
                                       force_ascii=False, indent=2)
        pd.DataFrame(df_clean).to_excel(f"data_output/raw/{timestamp}-products_clean.xlsx", index=False)

        logger.info("Running analysis and exporting reports...")
        analysis = AnalysisEngine(pd.DataFrame(df_clean))
        analysis.export_all(data_dir="data_output")

        logger.info("All exports completed successfully.")
        logger.info("Pipeline completed successfully!")

    except Exception:
        logger.exception("Pipeline failed due to an error:")
        raise


if __name__ == "__main__":
    main()
