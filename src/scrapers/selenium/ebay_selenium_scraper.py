import random
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.scrapers.base_scraper import BaseScraper
from src.utils.logger import get_logger

logger = get_logger("ebay-selenium")


def parse_price(price_str):
    try:
        if price_str:
            price = price_str.replace(",", "").replace("$", "").split()[0]
            return float(price)
        return None
    except Exception:
        return None


def clean_product_fields(prod):
    p = prod.copy()
    if isinstance(p.get('price'), str):
        price_clean = re.sub(r'[^\d.,]', '', p['price'])
        try:
            p['price'] = float(price_clean.replace(',', ''))
        except:
            p['price'] = None
    return p


def parse_product(product_html):
    title = None
    title_tag = product_html.select_one(".s-item__title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        if not title or "results for" in title:
            title = None

    url_tag = product_html.select_one("a.s-item__link")
    url = url_tag['href'] if url_tag and url_tag.has_attr('href') else None

    price_tag = product_html.select_one(".s-item__price")
    price = price_tag.get_text(strip=True) if price_tag else None

    img_tag = product_html.select_one(".s-item__image-img")
    img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

    condition_tag = product_html.select_one(".SECONDARY_INFO")
    condition = condition_tag.get_text(strip=True) if condition_tag else None

    shipping_tag = product_html.select_one(".s-item__shipping")
    shipping = shipping_tag.get_text(strip=True) if shipping_tag else None

    location_tag = product_html.select_one(".s-item__location")
    seller_location = location_tag.get_text(strip=True) if location_tag else None

    seller_tag = product_html.select_one(".s-item__seller-info-text")
    seller = seller_tag.get_text(strip=True) if seller_tag else None

    product = {
        'title': title,
        'price': price,
        'url': url,
        'review_count': -1,
        'rating': -1,
        'img_url': img_url,
    }
    return clean_product_fields(product)


agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

from src.scrapers.factory import ScraperFactory


@ScraperFactory.register('ebay')
class EbaySeleniumScraper(BaseScraper):
    """
    Selenium scraper for extracting product information from eBay search pages.
    Usage:
        scraper = EbaySeleniumScraper(config)
        data = scraper.scrape(category_url)
        scraper.close()
    """
    is_scrapy = False

    def __init__(self, config):
        self.user_agents = config.get("user_agents", agents)
        self.max_retries = config.get("max_retries", 3)
        self.base_url = config['base_url']
        self.categories = config['categories']
        self.max_pages = config['max_pages']
        self.delay = config['delay']
        self.driver = self._init_driver()
        logger.info("EbaySeleniumScraper initialized.")

    def _init_driver(self):
        options = Options()
        options.add_argument("--headless")
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"user-agent={user_agent}")
        logger.info(f"Selected User-Agent: {user_agent}")
        return webdriver.Chrome(options=options)

    def wait_for_products(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.s-item"))
            )
        except Exception as e:
            logger.warning("Timed out waiting for eBay product content.")

    def is_captcha_page(self):
        src = self.driver.page_source
        return (
                "detected unusual traffic" in src.lower() or
                "please verify you are a human" in src.lower() or
                "/challenge?" in self.driver.current_url
        )

    def fetch(self, url, retries=None):
        retries = retries if retries is not None else self.max_retries
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Fetching URL (attempt {attempt}): {url}")
                self.driver.get(url)
                time.sleep(random.uniform(self.delay, self.delay + 2))
                self.wait_for_products()
                return self.driver.page_source
            except Exception as e:
                if self.is_captcha_page():
                    logger.warning("CAPTCHA detected. Use proxy/user-agent rotation or solve manually.")
                    self.driver.save_screenshot(f"logs/ebay_captcha_{int(time.time())}.png")
                    break
                else:
                    logger.error(f"Error fetching page on attempt {attempt}: {e}", exc_info=True)
                    if attempt < retries:
                        logger.info("Retrying fetch...")
                        self.driver.quit()
                        self.driver = self._init_driver()
                        time.sleep(2)
                    else:
                        logger.error("Max fetch retries reached.")
                        raise
        return self.driver.page_source

    def parse(self, html):
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("li.s-item")
        all_products = []
        for product_html in products:
            data = parse_product(product_html)
            if data.get('title'):
                all_products.append(data)
        logger.info(f"Parsed {len(all_products)} valid products from page.")
        return all_products

    def scrape_category(self, category_url, max_pages=None, delay=None):
        all_products = []
        max_pages = max_pages or self.max_pages
        delay = delay or self.delay

        self.driver.get(category_url)
        for page in range(1, max_pages + 1):
            logger.info(f"Scraping eBay page {page}: {self.driver.current_url}")
            self.wait_for_products()
            html = self.driver.page_source
            page_products = self.parse(html)
            logger.info(f"Found {len(page_products)} products on page {page}.")
            all_products.extend(page_products)
            time.sleep(delay)

            if page < max_pages:
                try:
                    next_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination__next, a[aria-label='Next page']"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    time.sleep(0.5)
                    actions = ActionChains(self.driver)
                    actions.move_to_element(next_btn).pause(0.2).click().perform()
                except TimeoutException:
                    logger.warning("No next page or next button not clickable after waiting.")
                    break
                except Exception as e:
                    logger.warning(f"Failed to click next: {e}", exc_info=True)
                    break

        logger.info(f"Scraping {self.driver.current_url} completed. Total products: {len(all_products)}")
        return all_products

    def scrape(self, url: str):
        logger.info(f"Starting scrape for URL: {url}")
        return self.scrape_category(url)

    def close(self):
        self.driver.quit()
        logger.info("Closed Selenium WebDriver.")
