from unittest.mock import MagicMock

import pytest
from scrapy.http import HtmlResponse, Request

from src.scrapers.scrapy_crawler.newegg_crawler.spriders.newegg_scrapy import (
    parse_price,
    parse_rating,
    parse_review_count,
    get_browser_headers,
    NeweggSpider,
    NeweggScrapyScraper
)


def test_parse_price_valid():
    assert parse_price(['1,234', '56']) == 1234.56
    assert parse_price(['1234', '.99']) == 1234.99
    assert parse_price(['1234']) == 1234.00
    assert parse_price(['', '']) is None


def test_parse_price_invalid():
    assert parse_price([None, None]) is None
    assert parse_price([]) is None
    assert parse_price(['abc', '99']) is None


def test_parse_rating():
    assert parse_rating('rating-5') == 5
    assert parse_rating('rating-10 xyz') == 10
    assert parse_rating('notarating') is None
    assert parse_rating(None) is None


def test_parse_review_count():
    assert parse_review_count('(1,234)') == 1234
    assert parse_review_count('(56)') == 56
    assert parse_review_count('no reviews') is None
    assert parse_review_count('') is None


def test_get_browser_headers():
    uas = ['UA1', 'UA2', 'UA3']
    for _ in range(10):
        headers = get_browser_headers(uas)
        assert headers['User-Agent'] in uas
        assert "Accept" in headers
        assert "Accept-Language" in headers


@pytest.fixture
def spider():
    return NeweggSpider(
        start_urls=["http://example.com"],
        config={},
        results=[],
        max_pages=1,
        categories={},
        user_agents=["UA"]
    )


def fake_response(url, body, meta=None, status=200):
    request = Request(url=url, meta=meta or {})
    response = HtmlResponse(url=url, body=body.encode("utf-8"), encoding="utf-8", request=request)
    response.status = status
    return response


def test_parse_product_found(spider):
    html = """
    <html><body>
        <div class="item-cell">
            <a class="item-title" href="http://example.com/prod">Test Laptop</a>
            <li class="price-current"><strong>1,000</strong><sup>99</sup></li>
            <a class="item-rating rating-4"></a>
            <span class="item-rating-num">(22)</span>
            <a class="item-img"><img src="http://example.com/img.jpg" /></a>
        </div>
        <a title="Next" href="/page2"></a>
    </body></html>
    """
    spider.results.clear()
    response = fake_response("http://example.com", html, meta={'category': 'laptops', 'page_num': 1})
    list(spider.parse(response))
    assert len(spider.results) == 1
    prod = spider.results[0]
    assert prod["title"] == "Test Laptop"
    assert prod["price"] == 1000.99
    assert prod["rating"] == 4
    assert prod["review_count"] == 22
    assert prod["img_url"] == "http://example.com/img.jpg"
    assert prod["url"] == "http://example.com/prod"
    assert prod["category"] == "laptops"


def test_parse_no_products(spider):
    html = "<html><body><div>No products</div></body></html>"
    response = fake_response("http://example.com", html, meta={'category': 'unknown', 'page_num': 1})
    results = list(spider.parse(response))
    assert spider.results == []


def test_parse_non_200(spider):
    html = "<html><body>Error</body></html>"
    response = fake_response("http://example.com", html, status=503)
    results = list(spider.parse(response))
    assert results == []


def test_handle_error(spider):
    failure = MagicMock()
    failure.value = MagicMock()
    failure.value.response = MagicMock()
    failure.value.response.status = 500
    failure.value.response.text = "error body"
    failure.request = MagicMock()
    failure.request.url = "http://example.com"
    spider.handle_error(failure)


def test_scraper_fetch_and_scrape(monkeypatch):
    config = {
        "base_url": "http://example.com",
        "categories": {"laptops": "/cat/laptops"},
        "user_agents": ["UA"],
        "delay": 0,
        "max_pages": 1,
    }
    scraper = NeweggScrapyScraper(config)

    mock_process = MagicMock()
    monkeypatch.setattr(
        "src.scrapers.scrapy_crawler.newegg_crawler.spriders.newegg_scrapy.CrawlerProcess",
        lambda settings: mock_process
    )

    mock_process.crawl = MagicMock()
    mock_process.start = MagicMock()
    mock_process.crawl.side_effect = lambda *args, **kwargs: kwargs["results"].append({"title": "Dummy"})

    results = scraper.fetch(["http://example.com/cat/laptops"])
    assert {"title": "Dummy"} in results
    mock_process.crawl.assert_called_once()
    mock_process.start.assert_called_once()
