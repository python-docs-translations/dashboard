from __future__ import annotations

import pycountry
from babel.languages import get_official_languages
from pycountry_convert import (
    country_alpha2_to_continent_code,
    convert_continent_code_to_continent_name,
)

# Cache: maps base language code (e.g. 'zh') to a set of continent names.
_language_continents: dict[str, set[str]] | None = None


def _build_language_continent_map() -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for country in pycountry.countries:
        try:
            continent_code = country_alpha2_to_continent_code(country.alpha_2)
            continent = convert_continent_code_to_continent_name(continent_code)
        except KeyError:
            continue
        official_languages = get_official_languages(
            country.alpha_2, regional=True, de_facto=True
        )
        for lang in official_languages:
            # babel uses underscores (e.g. 'mn_Mong', 'sr_Latn'); strip the
            # script/variant suffix to get the bare language subtag.
            base = lang.split('_')[0]
            mapping.setdefault(base, set()).add(continent)
    return mapping


def get_language_continents(language_code: str) -> list[str]:
    """Return a sorted list of continents where *language_code* is official.

    A language may appear in multiple continents.  The base language tag
    (everything before the first ``-``) is used for the lookup so that, for
    example, both ``zh-cn`` and ``zh-tw`` resolve to the countries that have
    Chinese as an official language.  Dashboard codes use hyphens (BCP 47),
    while babel returns underscore-separated tags; the two separators are
    handled independently in :func:`_build_language_continent_map` and here.
    """
    global _language_continents
    if _language_continents is None:
        _language_continents = _build_language_continent_map()
    base = language_code.split('-')[0]
    return sorted(_language_continents.get(base, set()))
