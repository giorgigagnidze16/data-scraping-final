import pytest

@pytest.fixture
def amazon_config():
    return {
        "base_url": "https://www.amazon.com",
        "categories": {"laptops": "/s?k=laptops"},
        "max_pages": 2,
        "delay": 1,
    }
