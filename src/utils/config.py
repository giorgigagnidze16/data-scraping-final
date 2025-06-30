import yaml


class ConfigLoader:
    """
    Loads and manages configuration from a YAML file.

    Typical usage:
        loader = ConfigLoader("config.yaml")
        conf = loader.get_config("section_name")

    Args:
        path (str): Path to the YAML config file.
    """

    def __init__(self, path):
        self.config = self.load_yaml(path)

    @staticmethod
    def load_yaml(path):
        """
        Loads a YAML file and returns its contents as a dict.

        Args:
            path (str): Path to the YAML file.

        Returns:
            dict: Parsed YAML contents.
        """
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_config(self, conf):
        """
        Retrieves a section or key from the loaded config.

        Args:
            conf (str): Key/section name to retrieve.

        Returns:
            dict: The config section if found, otherwise an empty dict.
        """
        return self.config.get(conf, {})
