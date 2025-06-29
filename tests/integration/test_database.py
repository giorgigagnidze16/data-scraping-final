import os
import sqlite3
import tempfile
import uuid

import numpy as np
import pandas as pd
import pytest

from src.data import database
from tests.fixtures.data.db_fixtures import in_memory_db
from tests.fixtures.data.db_fixtures import sample_products


def test_save_and_load_products_raw(in_memory_db, sample_products):
    database.save_products_raw(sample_products)
    df = database.load_products_raw(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    titles = set(df["title"])
    assert "Acer Aspire 5" in titles
    database.save_products_raw([sample_products[0]])
    df2 = database.load_products_raw(as_dataframe=True)
    assert len(df2) == 2


def test_save_and_load_products(in_memory_db, sample_products):
    database.save_products(sample_products)
    df = database.load_products(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert set(df["title"]) == {"Acer Aspire 5", "HP Pavilion"}
    products_dict = database.load_products(as_dataframe=False)
    assert isinstance(products_dict, list)
    assert products_dict[0]["title"] in ["Acer Aspire 5", "HP Pavilion"]


def test_utils_convert_tuple_keys_to_str():
    obj = {('a', 1): {'b': 2}}
    res = database.convert_tuple_keys_to_str(obj)
    assert "a_1" in res


def test_utils_convert_for_json():
    df = pd.DataFrame([{"a": 1, "b": 2}])
    res = database.convert_for_json(df)
    assert isinstance(res, list) and isinstance(res[0], dict)


def test_utils_sanitize_for_json():
    obj = {"a": float("nan"), "b": float("inf"), "c": np.nan, "d": pd.Timestamp("2024-06-29")}
    cleaned = database.sanitize_db_for_json(obj)
    assert cleaned["a"] is None and cleaned["b"] is None and cleaned["c"] is None
    assert isinstance(cleaned["d"], str) and cleaned["d"].startswith("2024-06-29")


def test_generate_run_id():
    run_id = database.generate_run_id()
    uuid_obj = uuid.UUID(run_id)
    assert str(uuid_obj) == run_id


def test_schema_init(in_memory_db, monkeypatch):
    schema = """
    CREATE TABLE IF NOT EXISTS dummy_table (id INTEGER PRIMARY KEY, name TEXT);
    """
    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write(schema)
        tf.flush()
        schema_path = tf.name

    monkeypatch.setattr("src.data.database._db_params", {
        "host": "",
        "port": "",
        "user": "",
        "password": "",
        "dbname": "",
    }, raising=False)

    class FakeConn(sqlite3.Connection):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.autocommit = True

    monkeypatch.setattr("psycopg2.connect", lambda **kwargs: FakeConn(":memory:"))
    database.init_db_with_sql(schema_path)
    os.unlink(schema_path)


def test_error_when_not_configured(monkeypatch):
    monkeypatch.setattr("src.data.database._Session", None, raising=False)
    with pytest.raises(Exception):
        database.save_products_raw([{"url": "x"}])
    with pytest.raises(Exception):
        database.load_products_raw()
    with pytest.raises(Exception):
        database.save_products([{"url": "x"}])
    with pytest.raises(Exception):
        database.load_products()


def test_init_db_error(monkeypatch):
    monkeypatch.setattr("src.data.database._engine", None, raising=False)
    monkeypatch.setattr("src.data.database._db_params", {}, raising=False)
    with pytest.raises(Exception):
        database.init_db_with_sql("schema.sql")
