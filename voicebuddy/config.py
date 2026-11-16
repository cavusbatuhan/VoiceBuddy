"""Settings: read config.toml."""

import tomllib

CONFIG_FILE = "config.toml"


def load_config():
    """Read config.toml and return it as a dictionary: section -> its settings."""
    # tomllib wants the file opened in binary mode ("rb").
    with open(CONFIG_FILE, "rb") as file:
        return tomllib.load(file)


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.config
    print(load_config())
