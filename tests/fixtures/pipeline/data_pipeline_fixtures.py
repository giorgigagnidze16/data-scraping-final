import pytest


@pytest.fixture
def config_file(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
database:
  host: ""
  port: 0
  user: ""
  password: ""
  dbname: ""
""")
    return str(config_path)


@pytest.fixture
def schema_file(tmp_path):
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text(
        "CREATE TABLE IF NOT EXISTS products_raw (id INTEGER PRIMARY KEY, title TEXT, price REAL, url TEXT UNIQUE);")
    return str(schema_path)


@pytest.fixture
def output_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return str(out)


@pytest.fixture
def products():
    return [
        {"title": "A", "price": 10, "url": "u1", "source": "amazon", "category": "laptops"},
        {"title": "B", "price": 20, "url": "u2", "source": "ebay", "category": "laptops"},
    ]
