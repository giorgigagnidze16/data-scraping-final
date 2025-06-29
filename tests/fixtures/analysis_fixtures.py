import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "title": ["A", "B", "C", "D"],
        "category": ["laptop", "laptop", "desktop", "desktop"],
        "source": ["amazon", "mc", "amazon", "mc"],
        "price": [1000, 1100, 900, 950],
        "rating": [4.5, 4.6, 4.3, 4.4],
        "review_count": [100, 200, 150, 100]
    })


@pytest.fixture
def minimal_df():
    return pd.DataFrame({
        "title": ["X"],
        "category": ["tablet"],
        "source": ["amazon"],
        "price": [100],
        "rating": [5.0],
        "review_count": [50]
    })
