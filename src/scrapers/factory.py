class ScraperFactory:
    _registry = {}

    @classmethod
    def register(cls, key):
        """
        Decorator to register a new scraper class with a key.
        """

        def decorator(scraper_cls):
            cls._registry[key.lower()] = scraper_cls
            return scraper_cls

        return decorator

    @classmethod
    def create_scraper(cls, key, config):
        """
        Instantiate a scraper by key (name).
        """
        scraper_cls = cls._registry.get(key.lower())
        if not scraper_cls:
            raise ValueError(f"Scraper '{key}' is not registered.")
        return scraper_cls(config)

    @classmethod
    def available_scrapers(cls):
        """
        Return a list of registered scraper keys.
        """
        return list(cls._registry.keys())
