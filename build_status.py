"""
Fetch build status of languages in the https://docs.python.org.

Yield a tuple of language code and a Boolean indicating
whether it is in the language switcher.
"""

import tomllib
from collections.abc import Generator

import requests


def get_languages() -> Generator[tuple[str, str]]:
    data = requests.get(
        'https://raw.githubusercontent.com/'
        'python/docsbuild-scripts/refs/heads/main/config.toml',
        timeout=10,
    ).text
    config = tomllib.loads(data)
    languages = config['languages']
    defaults = config['defaults']
    for code, language in languages.items():
        language_code = code.lower().replace('_', '-')
        in_switcher = language.get('in_prod', defaults['in_prod'])
        yield language_code, in_switcher


def main() -> None:
    languages = {language: in_switcher for language, in_switcher in get_languages()}
    print(languages)
    for code in ('en', 'pl', 'ar', 'zh-cn', 'id'):
        print(f'{code}: {code in languages} {languages.get(code)}')


if __name__ == '__main__':
    main()
