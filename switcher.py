"""
Fetch languages in the https://docs.python.org language switcher.

Return a defaultdict mapping language codes to a Boolean indicating
whether it is in the language switcher.
"""

import tomllib
from collections import defaultdict
from typing import Generator

import requests


def get_languages() -> Generator[str, None, None]:
    data = requests.get(
        "https://raw.githubusercontent.com/"
        "python/docsbuild-scripts/refs/heads/main/config.toml",
        timeout=10,
    ).text
    config = tomllib.loads(data)
    languages = config["languages"]
    defaults = config["defaults"]
    for code, language in languages.items():
        if language.get("in_prod", defaults["in_prod"]):
            yield code.lower().replace("_", "-")


def main() -> None:
    languages = list(get_languages())
    print(languages)
    for code in ("en", "pl", "ar", "zh-cn"):
        print(f"{code}: {code in languages}")


if __name__ == "__main__":
    main()
