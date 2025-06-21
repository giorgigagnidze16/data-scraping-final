import random
import re
import time

import requests
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.utils.logger import get_logger

logger = get_logger("microcenter-static")


class MicroCenterStaticScraper(BaseScraper):
    """
    Static OOP scraper for Micro Center (category/search pages).
    """

    def __init__(self, config):
        self.user_agents = config.get("user_agents", [])
        self.max_retries = config.get("max_retries", 3)
        self.base_url = config["base_url"]
        self.categories = config["categories"]
        self.max_pages = config.get("max_pages", 1)
        self.delay = config.get("delay", 1)
        self.cookies = config.get("cookies", {})
        self.session = requests.Session()
        logger.info("MicroCenterStaticScraper initialized.")

    def fetch(self, url: str):
        for attempt in range(1, self.max_retries + 1):
            headers = {
                "User-Agent": random.choice(self.user_agents) if self.user_agents else None,
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.microcenter.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            }
            try:
                logger.info(f"Fetching URL (attempt {attempt}): {url}")
                resp = self.session.get(url, headers=headers, cookies=self.cookies, timeout=20)
                if resp.status_code == 200:
                    return resp.text
                else:
                    logger.warning(f"Non-200 response: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Request failed: {e}")
            if attempt < self.max_retries:
                logger.info("Retrying fetch...")
                time.sleep(self.delay)
        raise RuntimeError(f"Failed to fetch page after {self.max_retries} attempts: {url}")

    def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        product_cards = soup.select('li.product_wrapper')
        products = []
        for card in product_cards:
            product = self.parse_product(card)
            if product and product.get('title') and product.get('price') is not None:
                products.append(product)
        logger.info(f"Parsed {len(products)} products from page.")
        return products

    def parse_product(self, card):
        # Title and URL
        title_tag = card.select_one('.h2 a')
        title = title_tag.get_text(strip=True) if title_tag else None
        url = f"https://www.microcenter.com{title_tag['href']}" if title_tag and title_tag.has_attr('href') else None

        # Image
        img_tag = card.select_one('.image2 img')
        img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

        # Price
        price = None
        price_tag = card.select_one(".price_wrapper .price span[itemprop='price']")
        if price_tag:
            price_txt = price_tag.get_text(strip=True)
            price_match = re.search(r"[\d,.]+", price_txt)
            if price_match:
                try:
                    price = float(price_match.group(0).replace(',', ''))
                except Exception:
                    price = None
        else:
            # fallback: grab from any .price span
            price_tag = card.select_one(".price_wrapper .price")
            if price_tag:
                price_txt = price_tag.get_text(strip=True)
                price_match = re.search(r"[\d,.]+", price_txt)
                if price_match:
                    try:
                        price = float(price_match.group(0).replace(',', ''))
                    except Exception:
                        price = None

        # SKU
        sku_tag = card.select_one('p.sku')
        sku = sku_tag.get_text(strip=True).replace("SKU:", "").strip() if sku_tag else None

        desc_tag = card.select_one('.pDescription')
        desc_tag.get_text(separator=' ', strip=True) if desc_tag else None

        return {
            'title': title,
            'price': price,
            'rating': -1,
            'review_count': -1,
            'url': url,
            'img_url': img_url,
        }

    def scrape(self, url: str):
        return self.scrape_category(url)

    def scrape_category(self, category_url, max_pages=None, delay=None):
        all_products = []
        max_pages = max_pages or self.max_pages
        delay = delay or self.delay

        for page in range(1, max_pages + 1):
            # Pagination: ?page=2 or &page=2 for search pages
            url = (
                f"{category_url}&page={page}" if "search_results.aspx" in category_url and page > 1
                else f"{category_url}?page={page}" if page > 1
                else category_url
            )
            html = self.fetch(url)
            page_products = self.parse(html)
            all_products.extend(page_products)
            logger.info(f"Scraped page {page}, found {len(page_products)} products.")
            if len(page_products) == 0:
                break
            time.sleep(self.delay)
        logger.info(f"Scraping completed. Total products: {len(all_products)}")
        return all_products

    def close(self):
        self.session.close()
