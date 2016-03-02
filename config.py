import yaml


class Config(dict):
    def __init__(self, d):
        d = {k: Config(d[k]) if type(d[k]) is dict else d[k] for k in d}
        super(Config, self).__init__(d)

    def __getattr__(self, attr):
        return self.get(attr)


_config_file = open("ci/config.yaml", "r")
config = Config(yaml.load(_config_file))
_config_file.close()
