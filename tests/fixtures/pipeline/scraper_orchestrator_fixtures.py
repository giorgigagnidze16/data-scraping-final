from unittest.mock import patch

import pytest


@pytest.fixture
def mock_config():
    return {
        "amazon": {
            "base_url": "https://example.com/",
            "categories": {"laptops": "/laptops", "monitors": "/monitors"}
        },
        "microcenter": {
            "base_url": "https://mc.com/",
            "categories": {"desktops": "/desktops"}
        }
    }


@pytest.fixture
def patched_config_loader(mock_config):
    with patch("src.pipeline.scraper_orchestrator.ConfigLoader") as MockLoader:
        instance = MockLoader.return_value
        instance.get_config.side_effect = lambda name: mock_config[name]
        yield


@pytest.fixture
def patched_threaded_scrape_executor():
    with patch("src.pipeline.scraper_orchestrator.threaded_scrape_executor") as mock_executor:
        yield mock_executor
