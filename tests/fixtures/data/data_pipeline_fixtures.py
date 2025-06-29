import pandas as pd
import pytest

from src.data.processors import ProductDataProcessor


@pytest.fixture
def raw_data():
    return pd.DataFrame([
        {"title": "A", "price": "10", "url": "u1", "rating": "4.5", "review_count": "20", "source": "AMAZON",
         "category": "Laptops"},
        {"title": None, "price": 99, "url": "u2", "rating": None, "review_count": 10, "source": "ebay",
         "category": "Tablets"},
        {"title": "B", "price": "-3", "url": "u3", "rating": "NaN", "review_count": None, "source": "Etsy",
         "category": "Other"},
        {"title": "A", "price": 10, "url": "u1", "rating": 4.5, "review_count": 20, "source": "AMAZON",
         "category": "Laptops"},
        {"title": "C", "price": 1e6, "url": "u4", "rating": 2.0, "review_count": "5", "source": "Shop",
         "category": "Gadgets"},
        {"title": "D", "price": "bad", "url": None, "rating": 4, "review_count": "0", "source": "Other",
         "category": "Misc"},
    ])


@pytest.fixture
def processor(raw_data):
    return ProductDataProcessor(raw_data)
