"""
Fetch build status of languages in the https://docs.python.org.

Yield a tuple of language code and a Boolean indicating
whether it is in the language switcher.
"""

import tomllib
from collections.abc import Iterator

from urllib3 import PoolManager


def get_languages(http: PoolManager) -> Iterator[tuple[str, bool]]:
    data = http.request(
        'GET',
        'https://raw.githubusercontent.com/python/docsbuild-scripts/refs/heads/main/config.toml',
    ).data
    config = tomllib.loads(data.decode())
    for code, language in config['languages'].items():
        language_code = code.lower().replace('_', '-')
        in_switcher = language.get('in_prod', config['defaults']['in_prod'])
        yield language_code, in_switcher


def main() -> None:
    languages = {
        language: in_switcher for language, in_switcher in get_languages(PoolManager())
    }
    print(languages)
    for code in ('en', 'pl', 'ar', 'zh-cn', 'id'):
        print(f'{code}: {code in languages} {languages.get(code)}')


if __name__ == '__main__':
    main()
