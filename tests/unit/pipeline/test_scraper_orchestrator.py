import pytest
from unittest.mock import patch, MagicMock, call

import src.pipeline.scraper_orchestrator as orchestrator_mod
from src.pipeline.scraper_orchestrator import ScraperOrchestrator

@pytest.fixture
def dummy_config():
    return {
        'amazon': {
            'base_url': 'https://a.com/',
            'categories': {'laptops': 'cat1', 'pcs': 'cat2'},
            'max_pages': 1,
        },
        'newegg': {
            'base_url': 'https://n.com/',
            'categories': {'monitors': 'c3'},
        }
    }

@pytest.fixture
def fake_registry():
    class FakeScrapy:
        is_scrapy = True

        def __init__(self, config):
            self.config = config

        def scrape(self, urls):
            return [
                {'url': urls[0], 'name': 'X', 'category': None},
                {'url': urls[1], 'name': 'Y'},
            ]

    class FakeThreaded:
        is_scrapy = False

        def __init__(self, config):
            self.config = config

        def some_scrape_func(self, *a, **kw): return [{'name': 'Z'}]

    return {'amazon': FakeScrapy, 'newegg': FakeThreaded}

@pytest.fixture(autouse=True)
def patch_config_and_factory(monkeypatch, dummy_config, fake_registry):
    class DummyCL:
        def __init__(self, path): pass
        def get_config(self, name): return dummy_config[name]

    monkeypatch.setattr(orchestrator_mod, "ConfigLoader", DummyCL)
    monkeypatch.setattr(orchestrator_mod.ScraperFactory, "available_scrapers", staticmethod(lambda: list(dummy_config.keys())))
    monkeypatch.setattr(orchestrator_mod.ScraperFactory, "_registry", fake_registry)
    yield

def test_constructor_loads_config_and_names():
    orch = ScraperOrchestrator("dummy.yaml")
    assert set(orch.scraper_names) == {"amazon", "newegg"}

@patch.object(orchestrator_mod, "logger")
def test_run_scraper_scrapy_success(mock_logger):
    orch = ScraperOrchestrator("dummy.yaml")
    products = orch._run_scraper("amazon")
    assert len(products) == 2
    for p in products:
        assert p["source"] == "amazon"
        assert "category" in p
    assert any("finished" in c[0][0] for c in mock_logger.info.call_args_list)

@patch.object(orchestrator_mod, "logger")
def test_run_scraper_scrapy_failure(mock_logger):
    class BrokenScrapy:
        is_scrapy = True
        def __init__(self, config): pass
        def scrape(self, urls): raise RuntimeError("fail")

    orchestrator_mod.ScraperFactory._registry["amazon"] = BrokenScrapy

    orch = ScraperOrchestrator("dummy.yaml")
    products = orch._run_scraper("amazon")
    assert products == []
    assert any("failed" in str(c) for c in mock_logger.error.call_args_list)

@patch.object(orchestrator_mod, "threaded_scrape_executor")
@patch.object(orchestrator_mod, "logger")
def test_run_scraper_threaded_success(mock_logger, mock_executor):
    mock_executor.return_value = {
        "monitors": [{"name": "Z"}]
    }
    orch = ScraperOrchestrator("dummy.yaml")
    products = orch._run_scraper("newegg")
    assert products == [{"name": "Z", "source": "newegg", "category": "monitors"}]
    assert mock_executor.called

@patch.object(orchestrator_mod, "threaded_scrape_executor")
@patch.object(orchestrator_mod, "logger")
def test_run_scraper_not_registered(mock_logger, mock_executor):
    orch = ScraperOrchestrator("dummy.yaml")
    orchestrator_mod.ScraperFactory._registry.pop("newegg", None)
    products = orch._run_scraper("newegg")
    assert products == []
    assert any("not registered" in str(c) for c in mock_logger.error.call_args_list)

@patch.object(orchestrator_mod, "ProcessPoolExecutor")
@patch.object(orchestrator_mod, "as_completed")
@patch.object(orchestrator_mod, "logger")
def test_run_all_success(mock_logger, mock_as_completed, mock_executor):
    orch = ScraperOrchestrator("dummy.yaml")
    fake_future1 = MagicMock()
    fake_future1.result.return_value = [{"name": "A"}]
    fake_future2 = MagicMock()
    fake_future2.result.return_value = [{"name": "B"}]
    mock_executor.return_value.__enter__.return_value = mock_executor
    mock_executor.submit.side_effect = [fake_future1, fake_future2]
    mock_as_completed.return_value = [fake_future1, fake_future2]

    products = orch.run_all(max_workers=2)
    assert products == [{"name": "A"}, {"name": "B"}]

@patch.object(orchestrator_mod, "ProcessPoolExecutor")
@patch.object(orchestrator_mod, "as_completed")
@patch.object(orchestrator_mod, "logger")
def test_run_all_future_raises(mock_logger, mock_as_completed, mock_executor):
    orch = ScraperOrchestrator("dummy.yaml")
    fake_future1 = MagicMock()
    fake_future1.result.side_effect = RuntimeError("fail")
    mock_executor.return_value.__enter__.return_value = mock_executor
    mock_executor.submit.return_value = fake_future1
    mock_as_completed.return_value = [fake_future1]
    products = orch.run_all(max_workers=1)
    assert products == []
    assert any("Scraper failed" in str(c) for c in mock_logger.error.call_args_list)
