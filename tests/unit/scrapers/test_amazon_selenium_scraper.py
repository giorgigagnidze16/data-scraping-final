from unittest.mock import patch, MagicMock

from src.scrapers.selenium.amazon_scraper import AmazonSeleniumScraper
from tests.fixtures.scraper.amazon_configs import amazon_config
from tests.fixtures.scraper.amazon_html import sample_amazon_product_html


@patch("src.scrapers.selenium.amazon_scraper.webdriver.Chrome")
def test_driver_initialized_with_user_agent(mock_chrome, amazon_config):
    scraper = AmazonSeleniumScraper(amazon_config)
    assert scraper.driver is mock_chrome.return_value
    scraper.close()


@patch("src.scrapers.selenium.amazon_scraper.webdriver.Chrome")
def test_fetch_success_and_waits_for_products(mock_chrome, amazon_config):
    mock_driver = MagicMock()
    mock_driver.page_source = "<html><body>SomeContent</body></html>"
    mock_chrome.return_value = mock_driver

    scraper = AmazonSeleniumScraper(amazon_config)
    scraper.wait_for_products = MagicMock()
    url = "https://www.amazon.com/s?k=laptops"

    html = scraper.fetch(url)
    assert "<body>SomeContent</body>" in html
    scraper.wait_for_products.assert_called()
    scraper.close()


@patch("src.scrapers.selenium.amazon_scraper.webdriver.Chrome")
def test_parse_returns_all_products(amazon_config, sample_amazon_product_html):
    scraper = AmazonSeleniumScraper(amazon_config)
    products = scraper.parse(sample_amazon_product_html)
    assert len(products) == 1
    assert products[0]['title'] == "Test Product"
    assert products[0]['price'] is not None
    scraper.close()


@patch("src.scrapers.selenium.amazon_scraper.webdriver.Chrome")
def test_scrape_category_handles_pagination_and_next(mock_chrome, amazon_config):
    mock_driver = MagicMock()
    mock_driver.page_source = """
    <div data-component-type='s-search-result'>
        <div class='sg-col-inner'>
            <h2><span>Page 1 Product</span></h2>
        </div>
    </div>
    """
    mock_driver.current_url = "https://www.amazon.com/s?k=laptops&page=1"
    mock_chrome.return_value = mock_driver

    scraper = AmazonSeleniumScraper(amazon_config)
    scraper.wait_for_products = MagicMock()
    scraper.parse = MagicMock(return_value=[{'title': 'Page 1 Product'}])
    next_btn = MagicMock()
    WebDriverWait_patch = patch("src.scrapers.selenium.amazon_scraper.WebDriverWait").start()
    WebDriverWait_patch.return_value.until.return_value = next_btn

    mock_driver.execute_script = MagicMock()
    ActionChains_patch = patch("src.scrapers.selenium.amazon_scraper.ActionChains").start()
    ActionChains_patch.return_value.move_to_element.return_value.pause.return_value.click.return_value.perform.return_value = None

    products = scraper.scrape_category("https://www.amazon.com/s?k=laptops", max_pages=2, delay=0)

    assert len(products) >= 1
    scraper.close()
    patch.stopall()


@patch("src.scrapers.selenium.amazon_scraper.webdriver.Chrome")
def test_close_quits_driver(mock_chrome, amazon_config):
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    scraper = AmazonSeleniumScraper(amazon_config)
    scraper.close()
    mock_driver.quit.assert_called()
