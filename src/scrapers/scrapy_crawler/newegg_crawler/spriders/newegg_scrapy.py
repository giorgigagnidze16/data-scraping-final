import random
import time

import scrapy
from scrapy.crawler import CrawlerProcess

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.factory import ScraperFactory
from src.utils.logger import get_logger

logger = get_logger("newegg-scrapy")

# ----------- ScraperAPI -------------
SCRAPERAPI_KEY = ""
SCRAPERAPI_ENDPOINT = f"http://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={{}}"


def parse_price(price_parts):
    try:
        if not price_parts or not price_parts[0]:
            return None
        main = price_parts[0].replace(',', '').strip()
        decimal = price_parts[1].strip() if len(price_parts) > 1 else '00'
        return float(f"{main}.{decimal.lstrip('.')}")
    except Exception:
        return None


def parse_rating(class_str):
    import re
    m = re.search(r'rating-(\d+)', class_str or "")
    return int(m.group(1)) if m else None


def parse_review_count(txt):
    import re
    m = re.search(r'\(([\d,]+)\)', txt or "")
    return int(m.group(1).replace(',', '')) if m else None


def get_browser_headers(user_agents):
    ua = random.choice(user_agents)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
    }


class NeweggSpider(scrapy.Spider):
    name = "newegg"
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': False,
    }

    def __init__(self, start_urls, config, results, max_pages=5, categories=None, user_agents=None, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = start_urls
        self.config = config
        self.results = results
        self.max_pages = max_pages
        self.category_map = categories or {}
        self.user_agents = user_agents or ["Mozilla/5.0"]
        self.request_count = 0

    def start_requests(self):
        for url in self.start_urls:
            api_url = SCRAPERAPI_ENDPOINT.format(url)
            meta = {
                'category': self.category_map.get(url, 'unknown'),
                'page_num': 1,
            }
            headers = get_browser_headers(self.user_agents)
            yield scrapy.Request(
                api_url,
                callback=self.parse,
                errback=self.handle_error,
                headers=headers,
                meta=meta,
                dont_filter=True,
            )

    def parse(self, response):
        self.request_count += 1
        logger.info(f"Response received: {response.url} | Status: {response.status} | Request #{self.request_count}")

        if response.status != 200:
            logger.error(f"Non-200 status code: {response.status} for URL: {response.url}")
            logger.debug(f"Partial body: {response.text[:500]}")
            return

        url = response.url
        category = response.meta.get('category') or self.category_map.get(url, 'unknown')
        page_num = response.meta.get('page_num', 1)

        product_selectors = [
            "div.item-cell",
            ".item-container",
            "[data-testid='product-item']",
            ".product-item"
        ]
        product_cards = []
        for selector in product_selectors:
            product_cards = response.css(selector)
            if product_cards:
                logger.info(f"Found products using selector: {selector}")
                break

        if not product_cards:
            logger.warning(f"No products found with any selector on {response.url}")
            logger.debug(f"Page content preview: {response.text[:1000]}")
            return

        found = 0
        for prod in product_cards:
            title_selectors = ["a.item-title::text", ".item-title::text", "h3 a::text", ".product-title::text"]
            url_selectors = ["a.item-title::attr(href)", ".item-title::attr(href)", "h3 a::attr(href)",
                             ".product-title::attr(href)"]
            title = None
            product_url = None
            for selector in title_selectors:
                title = prod.css(selector).get()
                if title:
                    break
            for selector in url_selectors:
                product_url = prod.css(selector).get()
                if product_url:
                    break
            price_main = (prod.css("li.price-current strong::text").get() or
                          prod.css(".price-current strong::text").get() or
                          prod.css(".price .price-main::text").get())
            price_dec = (prod.css("li.price-current sup::text").get() or
                         prod.css(".price-current sup::text").get() or
                         prod.css(".price .price-decimal::text").get())
            price = parse_price([price_main, price_dec])
            rating_class = prod.css("a.item-rating::attr(class)").get()
            rating = parse_rating(rating_class)
            review_txt = prod.css("span.item-rating-num::text").get()
            review_count = parse_review_count(review_txt)
            img_url = (prod.css("a.item-img img::attr(src)").get() or
                       prod.css("a.item-img img::attr(data-src)").get() or
                       prod.css("img::attr(src)").get())
            if title and product_url:
                self.results.append({
                    "title": title.strip(),
                    "price": price,
                    "rating": rating,
                    "review_count": review_count,
                    "url": product_url,
                    "img_url": img_url,
                    "category": category,
                })
                found += 1

        logger.info(f"Found {found} products for category {category} on page {page_num}")

        if page_num < self.max_pages and found > 0:
            next_selectors = [
                'a[title="Next"]::attr(href)',
                'a[aria-label="Next"]::attr(href)',
                '.pagination .next::attr(href)',
                '.pager .next::attr(href)'
            ]
            next_page = None
            for selector in next_selectors:
                next_page = response.css(selector).get()
                if next_page:
                    break
            if next_page:
                delay = random.uniform(2, 5)
                time.sleep(delay)
                api_url = SCRAPERAPI_ENDPOINT.format(response.urljoin(next_page))
                meta = {
                    'category': category,
                    'page_num': page_num + 1,
                }
                headers = get_browser_headers(self.user_agents)
                yield scrapy.Request(
                    api_url,
                    callback=self.parse,
                    errback=self.handle_error,
                    headers=headers,
                    meta=meta,
                    dont_filter=True,
                )

    def handle_error(self, failure):
        response = getattr(failure.value, 'response', None)
        request = failure.request if hasattr(failure, "request") else None
        status = response.status if response else "NO_RESPONSE"
        logger.error(
            f"Request failed: {request.url if request else 'UNKNOWN'} | Status: {status}"
        )
        if response:
            logger.debug(f"Body snippet: {response.text[:400]}")


@ScraperFactory.register('newegg')
class NeweggScrapyScraper(BaseScraper):
    is_scrapy = True

    def __init__(self, config):
        self.config = config

    def fetch(self, urls):
        return self.scrape(urls)

    def parse(self, content):
        pass

    def scrape(self, urls):
        results = []
        categories = self.config.get("categories", {})
        url_to_category = {self.config["base_url"] + v: k for k, v in categories.items()}
        start_urls = [self.config["base_url"] + v for v in categories.values()]
        user_agents = self.config.get("user_agents", ["Mozilla/5.0"])

        process = CrawlerProcess(settings={
            "LOG_ENABLED": False,
            "DOWNLOAD_DELAY": self.config.get("delay", 2),
            "RANDOMIZE_DOWNLOAD_DELAY": 1,
            "COOKIES_ENABLED": True,
            "ROBOTSTXT_OBEY": False,
            "RETRY_TIMES": self.config.get("max_retries", 2),
            "RETRY_HTTP_CODES": [429, 500, 502, 503, 504, 522, 524, 408],
            "CONCURRENT_REQUESTS": 1,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
            "AUTOTHROTTLE_ENABLED": True,
            "AUTOTHROTTLE_START_DELAY": 2,
            "AUTOTHROTTLE_MAX_DELAY": 10,
            "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
            "DOWNLOADER_MIDDLEWARES": {
                'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            }
        })

        max_pages = self.config.get("max_pages", 5)
        process.crawl(
            NeweggSpider,
            start_urls=start_urls,
            config=self.config,
            results=results,
            max_pages=max_pages,
            categories=url_to_category,
            user_agents=user_agents,
        )
        process.start()
        logger.info(f"Scraped {len(results)} Newegg products.")
        return results

    def close(self):
        pass
