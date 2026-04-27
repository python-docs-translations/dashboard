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

    When the code contains a region subtag (e.g. ``pt-br``), the continent is
    resolved from that specific country (``BR`` → South America) rather than
    from all countries where the base language is spoken.  This prevents, for
    example, ``pt-br`` from appearing under Europe and Africa simply because
    Portuguese is also spoken there.

    When there is no region subtag, a language may appear in multiple
    continents.  Dashboard codes use hyphens (BCP 47), while babel returns
    underscore-separated tags; the two separators are handled independently in
    :func:`_build_language_continent_map` and here.
    """
    parts = language_code.split('-')

    # If there is a region subtag (2-letter, e.g. 'br' in 'pt-br'), resolve
    # the continent directly from that country.
    if len(parts) >= 2:
        region = parts[-1].upper()
        try:
            continent_code = country_alpha2_to_continent_code(region)
            return [convert_continent_code_to_continent_name(continent_code)]
        except KeyError:
            pass

    # No region subtag (or region unrecognised): return all continents where
    # the base language is an official language.
    global _language_continents
    if _language_continents is None:
        _language_continents = _build_language_continent_map()
    base = parts[0]
    return sorted(_language_continents.get(base, set()))
