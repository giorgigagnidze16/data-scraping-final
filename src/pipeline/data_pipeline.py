import os

from src.analysis.analysis_engine import AnalysisEngine
from src.data import database
from src.data.processors import ProductDataProcessor
from src.utils.config import ConfigLoader
from src.utils.logger import get_logger

logger = get_logger("pipeline")


class DataPipeline:
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
        logger.info(f"Saving {len(products)} raw scraped products to products_raw table...")
        database.save_products_raw(products)
        logger.info(f"Saved {len(products)} raw products.")

    def process_products(self):
        logger.info("Loading raw products from DB for cleaning...")
        df_raw = database.load_products_raw()
        processor = ProductDataProcessor(df_raw)
        processor.clean_and_validate()
        df_clean = processor.get_df()
        logger.info(f"Saving {len(df_clean)} cleaned products to products table...")
        database.save_products(df_clean.to_dict(orient='records'))
        return df_clean

    def analyze_and_store(self, df_clean, run_id):
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
        comparative_path_csv = os.path.join(self.output_dir, "comparative_analysis.csv")
        comparative_path_json = os.path.join(self.output_dir, "comparative_analysis.json")
        comparative.to_csv(comparative_path_csv, index=False)
        comparative.to_json(comparative_path_json, orient="records", indent=2)
        logger.info(f"Comparative analysis exported to: {comparative_path_csv} and {comparative_path_json}")

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
        logger.info("=== Data Pipeline Started ===")
        self.store_raw(all_products)
        df_clean = self.process_products()
        run_id = database.generate_run_id()
        self.analyze_and_store(df_clean, run_id)
        logger.info("=== Data Pipeline Finished ===")
        return df_clean
