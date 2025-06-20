from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self, url: str):
        pass

    @abstractmethod
    def parse(self, content: str):
        pass

    def scrape(self, url: str):
        html = self.fetch(url)
        return self.parse(html)
