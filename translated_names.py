import tomllib
from collections.abc import Iterator

from babel import Locale
from babel.core import UnknownLocaleError
from urllib3 import PoolManager


def babel_autonym(code: str) -> str | None:
    """Get the translated name for a language code with Babel"""
    try:
        locale = Locale.parse(code.replace('-', '_'))
        return locale.get_display_name(locale)
    except (UnknownLocaleError, ValueError):
        return None


def get_languages(http: PoolManager) -> Iterator[tuple[str, str]]:
    """
    Fetch languages built through docsbuild-scripts.
    Yields language codes and translated language names.
    """
    data = http.request(
        'GET',
        'https://raw.githubusercontent.com/python/docsbuild-scripts/refs/heads/main/config.toml',
    ).data
    config = tomllib.loads(data.decode())
    for code, language in config['languages'].items():
        language_code = code.lower().replace('_', '-')
        translated_name = language.get('translated_name')
        yield language_code, translated_name
