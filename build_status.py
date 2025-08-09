"""
Fetch translated names of languages.

Yield a tuple of language code and a string with the translated name.
"""

import tomllib
from collections.abc import Iterator

from urllib3 import PoolManager


def get_languages(http: PoolManager) -> Iterator[tuple[str, str]]:
    data = http.request(
        'GET',
        'https://raw.githubusercontent.com/python/docsbuild-scripts/refs/heads/main/config.toml',
    ).data
    config = tomllib.loads(data.decode())
    for code, language in config['languages'].items():
        language_code = code.lower().replace('_', '-')
        translated_name = language.get('translated_name')
        yield language_code, translated_name
