import numpy as np
import pandas as pd
import pytest

from src.data.processors import ProductDataProcessor
from tests.fixtures.data.data_pipeline_fixtures import processor, raw_data


def test_clean_and_validate_removes_invalid_and_duplicates(processor):
    proc = processor.clean_and_validate()
    df = proc.get_df()
    assert len(df) == 3
    assert not df.duplicated(subset=['url']).any()
    assert df['title'].isnull().sum() == 0
    assert df['url'].isnull().sum() == 0
    assert (df['price'].isnull().sum() == 0)


def test_clean_and_validate_numeric_and_lowercase(processor):
    df = processor.clean_and_validate().get_df()
    assert df['price'].dtype in [float, np.float64]
    assert df['rating'].dtype in [float, np.float64]
    assert df['review_count'].dtype == int
    assert (df['source'] == df['source'].str.lower()).all()
    assert (df['category'] == df['category'].str.lower()).all()


def test_export_csv(tmp_path, processor):
    processor.clean_and_validate()
    filename = tmp_path / "out.csv"
    processor.export(str(filename), "csv")
    result = pd.read_csv(filename)
    assert not result.empty


def test_export_excel(tmp_path, processor):
    processor.clean_and_validate()
    filename = tmp_path / "out.xlsx"
    processor.export(str(filename), "excel")
    result = pd.read_excel(filename)
    assert not result.empty


def test_export_json(tmp_path, processor):
    processor.clean_and_validate()
    filename = tmp_path / "out.json"
    processor.export(str(filename), "json")
    result = pd.read_json(filename)
    assert not result.empty


def test_export_invalid_type(processor):
    processor.clean_and_validate()
    with pytest.raises(ValueError):
        processor.export("file.unsupported", "unsupported")


def test_chaining_returns_self(processor):
    proc2 = processor.clean_and_validate()
    assert isinstance(proc2, ProductDataProcessor)
    proc3 = proc2.export("test.csv", "csv")
    assert isinstance(proc3, ProductDataProcessor)


def test_data_quality_report(processor):
    processor.clean_and_validate()
    report = processor.get_data_quality_report()
    expected_keys = {
        "total_rows", "missing_titles", "missing_prices", "missing_urls",
        "missing_ratings", "duplicate_urls", "negative_prices", "outlier_prices"
    }
    assert set(report.keys()) == expected_keys
    assert report["missing_titles"] == 0
    assert report["duplicate_urls"] == 0
    assert report["negative_prices"] >= 0
    assert report["outlier_prices"] >= 0
    assert report["total_rows"] == len(processor.get_df())


def test_edge_cases():
    df = pd.DataFrame([
        {"title": None, "price": None, "url": None}
    ])
    proc = ProductDataProcessor(df)
    proc.clean_and_validate()
    assert proc.get_df().empty
    df = pd.DataFrame([
        {"title": "A", "price": -1, "url": "u1"}
    ])
    proc = ProductDataProcessor(df)
    proc.clean_and_validate()
    report = proc.get_data_quality_report()
    assert report["negative_prices"] == 1
