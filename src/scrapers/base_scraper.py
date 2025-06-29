from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
    Abstract base scraper defining essential methods for other scrapers
    """

    @abstractmethod
    def fetch(self, url: str):
        """
        fetches the page content of the provided associated url
        """
        pass

    @abstractmethod
    def parse(self, content: str):
        """
        parses search results page and returns a list of product dicts.
        """
        pass

    def scrape(self, url: str):
        """
        Returns a list of all parsed product dictionaries found across all pages.
        """
        html = self.fetch(url)
        return self.parse(html)
