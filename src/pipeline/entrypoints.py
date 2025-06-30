import os
from datetime import datetime

import pandas as pd

from src.analysis.analysis_engine import AnalysisEngine
from src.pipeline.data_pipeline import DataPipeline
from src.pipeline.scraper_orchestrator import ScraperOrchestrator
from src.utils.logger import get_logger

logger = get_logger("main")


def run_scrapers(scrapers_config="config/scrapers.yaml", max_workers=4, save_path=None):
    logger.info("Starting scraper orchestrator...")
    orchestrator = ScraperOrchestrator(scrapers_config_path=scrapers_config)
    all_products = orchestrator.run_all(max_workers)
    logger.info(f"Scraping complete. {len(all_products)} products collected.")
    if save_path:
        df = pd.DataFrame(all_products)
        df.to_json(save_path, orient="records", force_ascii=False, indent=2)
        logger.info(f"Raw scraped products saved to {save_path}")
    return all_products


def process_pipeline(
        products=None,
        raw_json_path=None,
        db_config="config/database.yaml",
        export_raw=True,
        output_dir="data_output"
):
    logger.info("Running data pipeline...")
    pipeline = DataPipeline(db_config_path=db_config)
    if products is None and raw_json_path:
        products = pd.read_json(raw_json_path)
        products = products.to_dict(orient="records")
    df_clean = pipeline.run_pipeline(products)
    logger.info(f"Cleaned DataFrame shape: {df_clean.shape}")
    if export_raw:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        outdir = f"{output_dir}/raw"
        os.makedirs(outdir, exist_ok=True)
        pd.DataFrame(df_clean).to_csv(f"{outdir}/{timestamp}-products_clean.csv", index=False)
        pd.DataFrame(df_clean).to_json(f"{outdir}/{timestamp}-products_clean.json", orient="records", force_ascii=False,
                                       indent=2)
        pd.DataFrame(df_clean).to_excel(f"{outdir}/{timestamp}-products_clean.xlsx", index=False)
        logger.info(f"Exported cleaned data to {outdir}")
    return df_clean


def analyze_and_report(df_clean, output_dir="data_output"):
    logger.info("Running analysis and exporting reports...")
    analysis = AnalysisEngine(pd.DataFrame(df_clean))
    analysis.export_all(data_dir=output_dir)
    logger.info("Analysis and reports exported successfully.")
