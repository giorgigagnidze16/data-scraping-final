# tests/unit/test_selenium_scraper.py

from unittest.mock import patch, MagicMock

import pytest

from src.scrapers.selenium_scraper import AmazonSeleniumScraper


@pytest.fixture
def sample_config():
    return {
        "base_url": "https://www.amazon.com",
        "categories": {"laptops": "/s?k=laptops"},
        "max_pages": 1,
        "delay": 1,
    }


@patch("src.scrapers.selenium_scraper.webdriver.Chrome")
def test_fetch_returns_html(mock_chrome, sample_config):
    mock_driver = MagicMock()
    mock_driver.page_source = "<html><body>Test</body></html>"
    mock_chrome.return_value = mock_driver

    scraper = AmazonSeleniumScraper(sample_config)
    url = "https://www.amazon.com/s?k=laptops"

    html = scraper.fetch(url)

    assert "<body>Test</body>" in html
    scraper.close()


def test_parse_returns_list(sample_config):
    scraper = AmazonSeleniumScraper(sample_config)
    html = """
    <html>
        <body>
            <div data-component-type='s-search-result'>
                <div class='sg-col-inner'>
                    <h2><span>Test Product</span></h2>
                    <h2><a href='/dp/test'>Test</a></h2>
                    <img class='s-image' src='test.jpg'/>
                    <span class='a-price-whole'>99</span>
                    <span class='a-price-fraction'>99</span>
                    <i class='a-icon-star'><span class='a-icon-alt'>4.5 out of 5 stars</span></i>
                    <span class='a-size-base s-underline-text'>(123)</span>
                </div>
            </div>
        </body>
    </html>
    """
    products = scraper.parse(html)
    assert isinstance(products, list)
    assert len(products) == 1
    assert products[0]['title'] == "Test Product"
    assert products[0]['price'] is not None
    assert products[0]['rating'] == "4.5"
    scraper.close()
