from tests.fixtures.pipeline.scraper_orchestrator_fixtures import mock_config, patched_config_loader, \
    patched_threaded_scrape_executor


def test_run_scraper_single(patched_config_loader, patched_threaded_scrape_executor):
    from src.pipeline.scraper_orchestrator import ScraperOrchestrator
    patched_threaded_scrape_executor.return_value = {
        "laptops": [{"title": "A", "price": 1}],
        "monitors": [{"title": "B", "price": 2}],
    }
    orchestrator = ScraperOrchestrator(scrapers_config_path="dummy.yaml")
    result = orchestrator._run_scraper("amazon", orchestrator.scraper_classes["amazon"])
    assert isinstance(result, list)
    assert result[0]["source"] == "amazon"
    assert result[0]["category"] == "laptops"


def test_run_all(patched_config_loader, patched_threaded_scrape_executor):
    from src.pipeline.scraper_orchestrator import ScraperOrchestrator
    patched_threaded_scrape_executor.side_effect = [
        {"laptops": [{"title": "A"}], "monitors": []},
        {"desktops": [{"title": "B"}]}
    ]
    orchestrator = ScraperOrchestrator(scrapers_config_path="dummy.yaml")
    all_products = orchestrator.run_all(max_workers=2)
    assert isinstance(all_products, list)
    titles = {p["title"] for p in all_products}
    assert "A" in titles and "B" in titles


def test_scraper_exception_handling(patched_config_loader, patched_threaded_scrape_executor):
    from src.pipeline.scraper_orchestrator import ScraperOrchestrator
    def side_effect(**kwargs):
        if kwargs.get("scraper_cls").__name__ == "AmazonSeleniumScraper":
            raise Exception("Scraper failed")
        return {"desktops": [{"title": "B"}]}

    patched_threaded_scrape_executor.side_effect = side_effect
    orchestrator = ScraperOrchestrator(scrapers_config_path="dummy.yaml")
    all_products = orchestrator.run_all(max_workers=2)
    assert isinstance(all_products, list)
    assert any(p["title"] == "B" for p in all_products)
