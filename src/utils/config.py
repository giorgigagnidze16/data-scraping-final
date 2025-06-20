import yaml

class ConfigLoader:
    def __init__(self, path="config/scrapers.yaml"):
        self.config = self.load_yaml(path)

    @staticmethod
    def load_yaml(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_site_config(self, site):
        return self.config.get(site, {})
