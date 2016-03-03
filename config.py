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
    def __init__(self, d):
        d = {k: Config(d[k]) if type(d[k]) is dict else d[k] for k in d}
        super(Config, self).__init__(d)

    def __getattr__(self, attr):
        return self.get(attr)


_config_file = open("ci_config.yaml", "r")
config = Config(yaml.load(_config_file))
_config_file.close()
