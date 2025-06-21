import yaml


class ConfigLoader:
    def __init__(self, path):
        self.config = self.load_yaml(path)

    @staticmethod
    def load_yaml(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_config(self, conf):
        return self.config.get(conf, {})