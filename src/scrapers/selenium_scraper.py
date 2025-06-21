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

logger = get_logger("amazon-selenium")


def extract_rating(node):
    tag = node.select_one("i.a-icon-star-mini span.a-icon-alt") \
          or node.select_one("i.a-icon-star span.a-icon-alt") \
          or node.select_one(".a-icon-alt")
    if tag and tag.get_text(strip=True):
        rating_text = tag.get_text(strip=True)
        m = re.match(r"([\d.]+)", rating_text)
        if m:
            return m.group(1)
    tag = node.select_one("span.a-size-small.a-color-base")
    if tag:
        m = re.match(r"([\d.]+)", tag.get_text(strip=True))
        if m:
            return m.group(1)
    return None


def extract_price(node):
    for price_tag in node.select(".a-offscreen"):
        text = price_tag.get_text(strip=True)
        if re.match(r'^[\$\€\£]\s?\d', text):
            return text

    whole = node.select_one(".a-price-whole")
    frac = node.select_one(".a-price-fraction")
    if whole and frac:
        return f"${whole.text.strip()}.{frac.text.strip()}"
    if whole:
        return f"${whole.text.strip()}"

    parent = node.find_parent() if hasattr(node, "find_parent") else None
    if parent:
        for price_tag in parent.select(".a-offscreen"):
            text = price_tag.get_text(strip=True)
            if re.match(r'^[\$\€\£]\s?\d', text):
                return text

    return None


agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def clean_product_fields(prod):
    p = prod.copy()
    if isinstance(p.get('price'), str):
        price_clean = re.sub(r'[^\d.,]', '', p['price'])
        try:
            p['price'] = float(price_clean.replace(',', ''))
        except:
            p['price'] = None
    if 'rating' in p and p['rating'] is not None:
        try:
            p['rating'] = float(str(p['rating']).replace(',', '').strip())
        except:
            p['rating'] = None
    if 'review_count' in p and p['review_count'] is not None:
        review_str = str(p['review_count']).replace(',', '').strip()
        try:
            p['review_count'] = int(review_str)
        except:
            p['review_count'] = 0
    return p


def parse_product(product_html):
    """
    extracts data from a single search result page block
    """
    sg_col_inner = product_html.select_one("div.sg-col-inner")

    title_tag = sg_col_inner.select_one("h2 span") if sg_col_inner else None
    title = title_tag.get_text(strip=True) if title_tag else None

    url_tag = sg_col_inner.select_one("h2 a") if sg_col_inner else None
    if not url_tag:
        url_tag = product_html.select_one("a[href*='/dp/']")
    url = f"https://www.amazon.com{url_tag['href']}" if url_tag and url_tag.has_attr('href') else None

    img_tag = sg_col_inner.select_one("img.s-image") if sg_col_inner else None
    img_url = img_tag['src'] if img_tag else None

    price = extract_price(sg_col_inner) if sg_col_inner else None
    if not price:
        price = extract_price(product_html)

    rating = extract_rating(sg_col_inner) if sg_col_inner else None
    if not rating:
        rating = extract_rating(product_html)

    review_cnt_tag = sg_col_inner.select_one(
        "div[data-cy='reviews-block'] span.a-size-small.puis-normal-weight-text"
    ) if sg_col_inner else None
    if not review_cnt_tag and sg_col_inner:
        review_cnt_tag = sg_col_inner.select_one("span.a-size-base.s-underline-text")
    review_cnt = review_cnt_tag.get_text(strip=True).strip("()") if review_cnt_tag else None

    product = {
        'title': title,
        'price': price,
        'rating': rating,
        'url': url,
        'review_count': review_cnt,
        'img_url': img_url
    }

    return clean_product_fields(product)


class AmazonSeleniumScraper(BaseScraper):
    """
    Selenium-based scraper for extracting product information from Amazon search or category pages.

    Usage:
        scraper = AmazonSeleniumScraper(config)
        data = scraper.scrape(category_url)  #  base class method
        scraper.close()
    """

    def __init__(self, config):
        self.user_agents = config.get("user_agents", agents)
        self.max_retries = config.get("max_retries", 3)
        self.base_url = config['base_url']
        self.categories = config['categories']
        self.max_pages = config['max_pages']
        self.delay = config['delay']
        self.driver = self._init_driver()
        logger.info("AmazonSeleniumScraper initialized.")

    def _init_driver(self):
        options = Options()
        options.add_argument("--headless")
        user_agent = random.choice(self.user_agents)
        options.add_argument(f"user-agent={user_agent}")
        logger.info(f"Selected User-Agent: {user_agent}")
        return webdriver.Chrome(options=options)

    def wait_for_products(self, timeout=20):
        """
        wait until product blocks are loaded.
        """
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )

    def is_captcha_page(self):
        """
        detects if a captcha is shown
        """
        src = self.driver.page_source
        return (
                "Type the characters you see in this image" in src or
                "/captcha/" in src or
                "enter the characters as they are shown in the image" in src
        )

    def fetch(self, url, retries=3):
        """
        loads the URL in the browser, waits for dynamic content, and handles CAPTCHA if needed.
        """
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
                    self.driver.save_screenshot(f"logs/captcha_{int(time.time())}.png")
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
        """
        parses search results page and returns a list of product dicts.
        """
        logger.debug("Parsing HTML page for products.")
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("div[data-component-type='s-search-result']")
        all_products = []
        for product_html in products:
            data = parse_product(product_html)
            if all(data.get(field) for field in data.keys()):
                all_products.append(data)
        logger.info(f"Parsed {len(all_products)} valid products from page.")
        return all_products

    def scrape_category(self, category_url, max_pages=None, delay=None):
        """
        scrapes pages for a given search results, supports pagination

        Args:
            category_url (str): URL of the search - category.
            max_pages (int, optional): Number of pages to scrape.
            delay (int, optional): Seconds to wait between pages.

        Returns:
            list: All product dicts found across all pages.
        """
        all_products = []
        max_pages = max_pages or self.max_pages
        delay = delay or self.delay

        self.driver.get(category_url)
        for page in range(1, max_pages + 1):
            logger.info(f"Scraping Amazon page {page}: {self.driver.current_url}")
            try:
                self.wait_for_products()
            except Exception as e:
                if self.is_captcha_page():
                    logger.warning("CAPTCHA detected. Solve or rotate proxy/user-agent.", e)
                    break
                else:
                    logger.error("Timed out waiting for product content.", e, exc_info=True)
                    break

            html = self.driver.page_source
            page_products = self.parse(html)
            logger.info(f"Found {len(page_products)} products on page {page}.")
            all_products.extend(page_products)
            time.sleep(delay)

            if page < max_pages:
                try:
                    self.driver.execute_script("""
                                    let cover = document.getElementById('nav-cover');
                                    if (cover) { cover.style.display = 'none'; }
                                """)
                    next_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.s-pagination-next:not(.s-pagination-disabled)"))
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

        logger.info(f"Scraping completed. Total products: {len(all_products)}")
        return all_products

    def scrape(self, url: str):
        """
        scrapers multiple pages for the given category/search results.
        Returns a list of all product dicts found across all pages.
        """
        logger.info(f"Starting scrape for URL: {url}")
        return self.scrape_category(url)

    def close(self):
        self.driver.quit()
        logger.info("Closed Selenium WebDriver.")
