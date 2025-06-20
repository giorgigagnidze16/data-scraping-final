import random
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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


class AmazonSeleniumScraper(BaseScraper):
    """
     Selenium-based scraper for extracting product information from Amazon category or search result pages.

    The scraper uses Selenium with a headless Chrome browser to render JavaScript-heavy Amazon pages,
    then parses the product listings using BeautifulSoup.

    Attributes:
        base_url (str): base amazon url
        categories: list of categories to scrape
        max_pages (int): number of pages to scrape per category.
        delay (int): delay in seconds between page requests.
        driver (webdriver.Chrome): Selenium WebDriver instance.
    """

    def __init__(self, config):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.base_url = config['base_url']
        self.categories = config['categories']
        self.max_pages = config['max_pages']
        self.delay = config['delay']

    def fetch(self, url):
        """
        Loads the given URL in the Selenium-driven browser and returns the rendered page HTML.

        Args:
            url (str): The URL.

        Returns:
            str: HTML of the rendered page.
        """
        self.driver.get(url)
        time.sleep(random.randint(self.delay, self.delay + 2))
        return self.driver.page_source

    def parse(self, html):
        sg_col_inner = html.select_one("div.sg-col-inner")

        title_tag = sg_col_inner.select_one("h2 span")
        title = title_tag.get_text(strip=True) if title_tag else None

        url_tag = sg_col_inner.select_one("h2 a")
        url = f"https://www.amazon.com{url_tag['href']}" if url_tag else None

        img_tag = sg_col_inner.select_one("img.s-image")
        img_url = img_tag['src'] if img_tag else None

        price = self.extract_price(sg_col_inner) or self.extract_price(html)

        rating = extract_rating(sg_col_inner) or extract_rating(html)

        review_cnt_tag = sg_col_inner.select_one(
            "div[data-cy='reviews-block'] span.a-size-small.puis-normal-weight-text")
        if not review_cnt_tag:
            review_cnt_tag = sg_col_inner.select_one("span.a-size-base.s-underline-text")
        review_cnt = review_cnt_tag.get_text(strip=True).strip("()") if review_cnt_tag else None

        url_tag = sg_col_inner.select_one("h2 a") if sg_col_inner else None
        if not url_tag:
            url_tag = html.select_one("a[href*='/dp/']")
        url = f"https://www.amazon.com{url_tag['href']}" if url_tag and url_tag.has_attr('href') else None

        return {
            'title': title,
            'price': price,
            'rating': rating,
            'url': url,
            'review_count': review_cnt,
            'img_url': img_url
        }

    def extract_price(self, node):
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

        parent = node.find_parent()
        if parent:
            for price_tag in parent.select(".a-offscreen"):
                text = price_tag.get_text(strip=True)
                if re.match(r'^[\$\€\£]\s?\d', text):
                    return text

        return None

    def scrape_category(self, category_url, max_pages=None, delay=None):
        all_products = []
        max_pages = max_pages or self.max_pages
        delay = delay or self.delay
        for page in range(1, max_pages + 1):
            url = f"{category_url}&page={page}"
            print(f"Scraping Amazon page: {url}")
            html = self.fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            products = soup.select("div[data-component-type='s-search-result']")
            for product in products:
                data = self.parse(product)
                print(data)
                if data["title"]:
                    all_products.append(data)
            time.sleep(delay)
        return all_products

    def close(self):
        self.driver.quit()
