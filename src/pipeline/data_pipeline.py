import json
import os
from datetime import datetime

from src.analysis.analysis_engine import AnalysisEngine
from src.data import database
from src.data.processors import ProductDataProcessor
from src.utils.config import ConfigLoader
from src.utils.logger import get_logger
from src.utils.utils import sanitize_db_for_json, convert_tuple_keys_to_str

logger = get_logger("pipeline")


class DataPipeline:
    """
    High-level data ETL pipeline for processing scraped product data.

    This pipeline coordinates the flow of data from raw scraping results through several stages:
    - Storing raw data in the database for traceability and audit
    - Cleaning and validating raw product records
    - Analyzing cleaned data and persisting summary analytics
    - Exporting cleaned datasets and analysis reports to files

    The pipeline expects configuration via a YAML file (database connection, etc.),
    and handles all directory creation for outputs.

    Typical usage:
        pipeline = DataPipeline("config/database.yaml")
        df_clean = pipeline.run_pipeline(all_products)

    Args:
        db_config_path (str): Path to the YAML file containing database configuration.
        schema_path (str): Optional path to SQL schema file for DB initialization.
        output_dir (str): Directory to store processed data and reports.
    """

    def __init__(self, db_config_path, schema_path="schema.sql", output_dir="data_output"):
        self.db_config = ConfigLoader(db_config_path).get_config("database")
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        database.configure_engine(
            self.db_config["host"],
            self.db_config["port"],
            self.db_config["user"],
            self.db_config["password"],
            self.db_config["dbname"]
        )
        database.init_db_with_sql(schema_path)

    def store_raw(self, products):
        """
        Persists a list of raw, unprocessed product dicts into the database.

        Args:
            products (List[dict]): Raw product items scraped from web sources.

        Effect:
            - Writes raw records to the 'products_raw' table.
            - Logs operation summary.
        """
        logger.info(f"Saving {len(products)} raw scraped products to products_raw table...")
        database.save_products_raw(products)
        logger.info(f"Saved {len(products)} raw products.")

    def process_products(self):
        """
        Loads raw products from DB, cleans and validates them, and stores cleaned results.

        Returns:
            pandas.DataFrame: The cleaned and validated products, ready for analysis.

        Effect:
            - Applies cleaning/validation logic via ProductDataProcessor.
            - Persists cleaned records to 'products' table in DB.
            - Logs processing and record count.
        """
        logger.info("Loading raw products from DB for cleaning...")
        df_raw = database.load_products_raw()
        processor = ProductDataProcessor(df_raw)
        processor.clean_and_validate()
        df_clean = processor.get_df()
        logger.info(f"Saving {len(df_clean)} cleaned products to products table...")
        database.save_products(df_clean.to_dict(orient='records'))
        return df_clean

    def analyze_and_store(self, df_clean, run_id):
        """
        Performs analysis on the cleaned products and stores results in both the DB and as files.

        For each unique source, and for all data, it:
            - Computes summary statistics, group-by stats (category, source), and trends.
            - Persists these analytics into database tables.
            - Exports cleaned datasets and reports to CSV/JSON for later inspection.

        Args:
            df_clean (pandas.DataFrame): Cleaned product data.
            run_id (str/int): Unique identifier for this pipeline execution (for traceability).

        Effect:
            - Creates timestamped output files in organized subdirectories.
            - Ensures all results are auditable and reproducible.
            - Logs each step and output location.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        processed_dir = os.path.join(self.output_dir, "processed")
        reports_dir = os.path.join(self.output_dir, "reports")
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        logger.info("Starting analysis and storing analysis results in DB...")
        for source in df_clean['source'].unique():
            df_source = df_clean[df_clean['source'] == source]
            analysis = AnalysisEngine(df_source)
            database.save_analysis_summary(run_id, source, analysis.overall_report())
            for group_type in ['category', 'source']:
                group_stats = getattr(analysis.stats_engine, f'by_{group_type}')()
                for field, stats in group_stats.items():
                    for group_value, stat in stats.items():
                        database.save_analysis_group_stats(run_id, group_type, group_value, source, stat)
            trends = analysis.trend_analysis()
            for trend_type, trend in trends.items():
                database.save_analysis_trends(run_id, trend_type, source,
                                              trend if isinstance(trend, dict) else trend.to_dict())
        analysis_all = AnalysisEngine(df_clean)
        comparative = analysis_all.comparative_analysis()

        products_clean_csv = os.path.join(processed_dir, f"products_clean_{timestamp}.csv")
        products_clean_json = os.path.join(processed_dir, f"products_clean_{timestamp}.json")
        df_clean.to_csv(products_clean_csv, index=False)
        df_clean.to_json(products_clean_json, orient="records", indent=2)
        logger.info(f"Processed products exported to: {products_clean_csv} and {products_clean_json}")

        comparative_path_csv = os.path.join(reports_dir, f"comparative_analysis_{timestamp}.csv")
        comparative_path_json = os.path.join(reports_dir, f"comparative_analysis_{timestamp}.json")
        comparative.to_csv(comparative_path_csv, index=False)
        comparative.to_json(comparative_path_json, orient="records", indent=2)
        logger.info(f"Comparative analysis exported to: {comparative_path_csv} and {comparative_path_json}")

        full_report = analysis_all.overall_report()
        full_report_path = os.path.join(reports_dir, f"full_report_{timestamp}.json")
        with open(full_report_path, "w", encoding="utf-8") as f:
            json.dump(convert_tuple_keys_to_str(sanitize_db_for_json(full_report)), f, indent=2)
        logger.info(f"Full report exported to: {full_report_path}")

        logger.info(f"Analysis and storage in DB complete for run_id={run_id}.")
        database.save_analysis_summary(run_id, "all", analysis_all.overall_report())
        for group_type in ['category', 'source']:
            group_stats = getattr(analysis_all.stats_engine, f'by_{group_type}')()
            for field, stats in group_stats.items():
                for group_value, stat in stats.items():
                    database.save_analysis_group_stats(run_id, group_type, group_value, "all", stat)
        trends_all = analysis_all.trend_analysis()
        for trend_type, trend in trends_all.items():
            database.save_analysis_trends(run_id, trend_type, "all",
                                          trend if isinstance(trend, dict) else trend.to_dict())
        logger.info(f"Analysis and storage in DB complete for run_id={run_id}.")

    def run_pipeline(self, all_products):
        """
        Runs the entire ETL pipeline: stores raw, cleans, analyzes, and exports data.

        Args:
            all_products (List[dict]): Raw product data (scraped, e.g. via Scrapy/Selenium).

        Returns:
            pandas.DataFrame: Cleaned products DataFrame.

        Steps:
            1. Stores all raw products to DB for auditing.
            2. Cleans and validates all records, stores cleaned output to DB.
            3. Runs analysis, exports reports, persists all analytics to DB.
            4. Returns cleaned product DataFrame for downstream use.

        Effect:
            - Provides end-to-end processing from raw scrape to actionable analytics.
            - All results are logged, timestamped, and easy to trace.
        """
        logger.info("=== Data Pipeline Started ===")
        self.store_raw(all_products)
        df_clean = self.process_products()
        run_id = database.generate_run_id()
        self.analyze_and_store(df_clean, run_id)
        logger.info("=== Data Pipeline Finished ===")
        return df_clean
