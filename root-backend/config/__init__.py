from .settings import config_by_name


def get_config(config_name=None):
    if config_name:
        return config_by_name.get(config_name, config_by_name["development"])

    from os import getenv

    env = getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, config_by_name["development"])
