from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

from src.analysis.analysis_engine import AnalysisEngine
from tests.fixtures.analysis_fixtures import sample_df, minimal_df


def test_feature_engineering_columns(sample_df):
    engine = AnalysisEngine(sample_df)
    df = engine.df
    assert "expensive" in df.columns
    assert "price_q_5" in df.columns
    assert "price_q_95" in df.columns
    assert "price_group" in df.columns
    assert "price_flag" in df.columns
    assert "outlier" in df.columns
    median = sample_df['price'].median()
    np.testing.assert_array_equal(df['expensive'], df['price'] > median)


def test_feature_engineering_single_value(minimal_df):
    engine = AnalysisEngine(minimal_df)
    df = engine.df
    assert (df["expensive"] == False).all()
    assert (df["price_group"] == "Low").all()
    assert "outlier" in df.columns


def test_summary_statistics(sample_df):
    engine = AnalysisEngine(sample_df)
    summary = engine.summary_statistics()
    assert isinstance(summary, dict)
    assert "price" in summary
    assert "median" in summary["price"]


def test_nulls_and_uniques(sample_df):
    engine = AnalysisEngine(sample_df)
    nulls = engine.nulls()
    uniques = engine.uniques()
    for col in sample_df.columns:
        assert col in nulls
        assert nulls[col] == 0
    assert uniques["category"] == 2


def test_by_source_and_by_category(sample_df):
    engine = AnalysisEngine(sample_df)
    src = engine.by_source()
    cat = engine.by_category()
    assert "price" in src
    assert "price" in cat


def test_trend_analysis(sample_df):
    engine = AnalysisEngine(sample_df)
    trends = engine.trend_analysis()
    assert "price_trend" in trends
    assert "review_trend" in trends
    assert isinstance(trends["price_trend"], pd.DataFrame)


def test_overall_report_keys(sample_df):
    engine = AnalysisEngine(sample_df)
    report = engine.overall_report()
    expected = {"summary", "nulls", "uniques", "by_source", "by_category", "trends"}
    assert set(report.keys()) == expected
    assert set(report["trends"].keys()) == {"price_trend", "review_trend"}


@patch("src.analysis.analysis_engine.ReportGenerator")
def test_export_all_calls_report_methods(mock_reportgen, sample_df, tmp_path):
    mock_instance = MagicMock()
    mock_reportgen.return_value = mock_instance
    data_dir = tmp_path / "out"
    data_dir.mkdir()
    engine = AnalysisEngine(sample_df)
    engine.export_all(str(data_dir))
    mock_reportgen.assert_called_once()
    mock_instance.to_json.assert_called_once()
    mock_instance.to_csv.assert_called_once()
    mock_instance.print_report.assert_called_once()


def test_comparative_analysis_mutual_cats(sample_df):
    engine = AnalysisEngine(sample_df)
    df_compare = engine.comparative_analysis()
    cats = set(df_compare["category"])
    assert cats == {"laptop", "desktop"}
    assert len(df_compare) == 4
    assert all(c in df_compare.columns for c in ["avg_price", "median_price", "count"])


def test_comparative_analysis_custom_features(sample_df):
    engine = AnalysisEngine(sample_df)
    result = engine.comparative_analysis(features=["price"])
    assert set(result.columns) >= {"avg_price", "median_price", "min_price", "max_price", "count"}


def test_comparative_analysis_no_mutuals(minimal_df):
    engine = AnalysisEngine(minimal_df)
    result = engine.comparative_analysis()
    assert result.empty
