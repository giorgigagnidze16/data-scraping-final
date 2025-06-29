import os
from unittest.mock import patch

import pandas as pd

from src.pipeline.data_pipeline import DataPipeline
from tests.fixtures.pipeline.data_pipeline_fixtures import config_file, schema_file, output_dir, products


@patch("src.data.database.save_analysis_trends")
@patch("src.data.database.save_analysis_group_stats")
@patch("src.data.database.save_analysis_summary")
@patch("src.data.database.load_products_raw", return_value=pd.DataFrame([
    {"title": "A", "price": 10, "url": "u1", "source": "amazon", "category": "laptops"},
    {"title": "B", "price": 20, "url": "u2", "source": "ebay", "category": "laptops"},
]))
@patch("src.data.database.save_products")
@patch("src.data.database.save_products_raw")
@patch("src.data.database.init_db_with_sql")
@patch("src.data.database.configure_engine")
@patch("src.pipeline.data_pipeline.AnalysisEngine")
def test_pipeline_end_to_end(
        MockEngine, mock_configure, mock_init_sql,
        mock_save_raw, mock_save_products, mock_load_raw,
        mock_save_summary, mock_save_group_stats, mock_save_trends,
        config_file, schema_file, output_dir, products
):
    MockEngine.return_value.overall_report.return_value = {}
    MockEngine.return_value.stats_engine.by_category.return_value = {}
    MockEngine.return_value.stats_engine.by_source.return_value = {}
    MockEngine.return_value.trend_analysis.return_value = {}
    MockEngine.return_value.comparative_analysis.return_value = pd.DataFrame([{"result": 1}])

    pipeline = DataPipeline(config_file, schema_path=schema_file, output_dir=output_dir)
    df_clean = pipeline.run_pipeline(products)
    assert not df_clean.empty

    reports_dir = os.path.join(output_dir, "reports")
    csv_files = [f for f in os.listdir(reports_dir) if f.startswith("comparative_analysis_") and f.endswith(".csv")]
    json_files = [f for f in os.listdir(reports_dir) if f.startswith("comparative_analysis_") and f.endswith(".json")]
    assert csv_files, f"No comparative_analysis_*.csv found in {reports_dir}"
    assert json_files, f"No comparative_analysis_*.json found in {reports_dir}"
