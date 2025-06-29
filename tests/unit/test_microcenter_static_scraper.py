from unittest.mock import patch, MagicMock
import pytest

from src.scrapers.static_scraper import MicroCenterStaticScraper
from tests.fixtures.microcenter_html import sample_microcenter_product_html
from tests.fixtures.microcenter_configs import microcenter_config

def test_parse_returns_all_products(microcenter_config, sample_microcenter_product_html):
    scraper = MicroCenterStaticScraper(microcenter_config)
    products = scraper.parse(sample_microcenter_product_html)
    assert len(products) == 1
    assert products[0]['title'] == "Sample Product"
    assert products[0]['price'] == 999.99
    scraper.close()

@patch("src.scrapers.static_scraper.requests.Session")
def test_fetch_success_and_headers(mock_session, microcenter_config):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html>works</html>"
    mock_session.return_value.get.return_value = mock_resp

    scraper = MicroCenterStaticScraper(microcenter_config)
    html = scraper.fetch("https://www.microcenter.com/search_results.aspx?N=4294967288")
    assert "works" in html
    scraper.close()

@patch("src.scrapers.static_scraper.requests.Session")
def test_fetch_retries_and_fails(mock_session, microcenter_config):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_session.return_value.get.return_value = mock_resp

    scraper = MicroCenterStaticScraper(microcenter_config)
    with pytest.raises(RuntimeError, match="Failed to fetch page after"):
        scraper.fetch("https://www.microcenter.com/search_results.aspx?N=4294967288")
    scraper.close()

def test_parse_product_handles_missing_fields(microcenter_config):
    html = """
    <html><body>
      <li class='product_wrapper'>
        <div class='h2'><a href='/product/1'></a></div>
        <!-- No price, no img -->
      </li>
    </body></html>
    """
    scraper = MicroCenterStaticScraper(microcenter_config)
    products = scraper.parse(html)
    assert len(products) == 0
    scraper.close()

def test_close_closes_session(microcenter_config):
    scraper = MicroCenterStaticScraper(microcenter_config)
    scraper.session = MagicMock()
    scraper.close()
    scraper.session.close.assert_called()
