import random
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.scrapers.base_scraper import BaseScraper


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


class AmazonSeleniumScraper(BaseScraper):
    """
    Selenium-based scraper for extracting product information from Amazon search or category pages.

    Usage:
        scraper = AmazonSeleniumScraper(config)
        data = scraper.scrape(category_url)  # Uses the base class method
        scraper.close()
    """

    def __init__(self, config):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.base_url = config['base_url']
        self.categories = config['categories']
        self.max_pages = config['max_pages']
        self.delay = config['delay']

    def wait_for_products(self, timeout=10):
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

    def fetch(self, url):
        """
        loads the URL in the browser, waits for dynamic content, and handles CAPTCHA if needed.
        """
        self.driver.get(url)
        time.sleep(random.uniform(self.delay, self.delay + 2))
        try:
            self.wait_for_products(timeout=12)
        except Exception:
            if self.is_captcha_page():
                print("[!] CAPTCHA detected. Use proxy/user-agent rotation or solve manually.")
            else:
                print("[!] Timed out waiting for product content.")
        return self.driver.page_source

    def parse(self, html):
        """
        parses search results page and returns a list of product dicts.
        """
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("div[data-component-type='s-search-result']")
        all_products = []
        for product_html in products:
            data = self.parse_product(product_html)
            if all(data.get(field) for field in data.keys()):
                all_products.append(data)
        return all_products

    def parse_product(self, product_html):
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

        return {
            'title': title,
            'price': price,
            'rating': rating,
            'url': url,
            'review_count': review_cnt,
            'img_url': img_url
        }

    def scrape_category(self, category_url, max_pages=None, delay=None):
        """
        Scrapes multiple pages for a given search results

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
            print(f"Scraping Amazon page {page}: {self.driver.current_url}")
            try:
                self.wait_for_products(timeout=12)
            except Exception:
                if self.is_captcha_page():
                    print("[!] CAPTCHA detected. Solve or rotate proxy/user-agent.")
                    break
                else:
                    print("[!] Timed out waiting for product content.")
                    break

            html = self.driver.page_source
            page_products = self.parse(html)
            print(f"  Found {len(page_products)} products.")
            all_products.extend(page_products)
            time.sleep(delay)

            if page < max_pages:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR,
                                                        "a.s-pagination-next:not(.s-pagination-disabled)")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(0.5)
                    next_btn.click()
                except Exception as e:
                    print(f"[!] No next page or failed to click next: {e}")
                    break

        return all_products

    def scrape(self, url: str):
        """
        scrapers multiple pages for the given category/search results.
        Returns a list of all product dicts found across all pages.
        """
        return self.scrape_category(url)

    def close(self):
        self.driver.quit()
