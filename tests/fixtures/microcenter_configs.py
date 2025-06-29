import pytest

@pytest.fixture
def microcenter_config():
    return {
        "base_url": "https://www.microcenter.com",
        "categories": {"laptops": "/search_results.aspx?N=4294967288"},
        "max_pages": 1,
        "delay": 0,
        "user_agents": ["Mozilla/5.0"],
        "cookies": {},
        "max_retries": 2,
    }
