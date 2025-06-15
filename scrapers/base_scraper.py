from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
     base class for web scrapers.

    A common interface for all scraper implementations with a 'scrape' method.
    """

    @abstractmethod
    def scrape(self, url: str):
        """
        Abstract method to perform web scraping on a given URL.

        This method must be implemented by any concrete subclass of BaseScraper.
        It is responsible for fetching content from the specified URL,
        parsing it, and extracting the relevant data.

        Args:
            url (str): The URL of the webpage to scrape.

        Raises:
            NotImplementedError: raised to indicate that the method must be
                                 overridden by subclasses.
        """
        raise NotImplementedError("Scrape method must be implemented.")
