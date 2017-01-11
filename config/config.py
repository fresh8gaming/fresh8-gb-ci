import yaml

___author___ = "Lee Archer (github.com/lbn)"
___credits___ = ["Jim Hill (github.com/jimah)",
                 "Lee Archer (github.com/lbn)"]
___license___ = "MIT"
___version___ = "1.0"
___maintainer___ = "Jim Hill"
___email___ = "jimi2204@googlemail.com"
___status___ = "Development"


class Config(dict):

    REQUIRED_PARENT_KEYS = ["all", "go_vet", "golint", "code_coverage"]
    REQUIRED_CHILD_KEYS = {
        "all": ["packages", "project_type", "ignored_commands"],
        "go_vet": ["ignored_packages"],
        "golint": ["ignored_packages"],
        "code_coverage": ["ignored_packages", "threshold"],
    }

    def __init__(self, d):
        d = {k: Config(d[k]) if type(d[k]) is dict else d[k] for k in d}
        super(Config, self).__init__(d)

    def __getattr__(self, attr):
        return self.get(attr)

    def validate_config(self, config_dict):
        """Validate configuration file.

        :param config_dict: dict
        :return bool: True if valid
        """
        if any(key not in config_dict for key in self.REQUIRED_PARENT_KEYS):
            return False
        for k, v in self.REQUIRED_CHILD_KEYS.items():
            if any(key not in config_dict[k] for key in v):
                return False
        return True


def get_config(file="ci_config.yaml"):
    with open(file, "r") as f:
        config = Config(yaml.load(f))
        if not config.validate_config(config):
            print(config)
            raise Exception("Missing config values")
        return config
