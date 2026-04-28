from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import git
import polib
import urllib3

from repositories import Language

RTD_TRANSLATIONS_URL = (
    'https://app.readthedocs.org/api/v3/projects/'
    'python-packaging-user-guide/translations/'
)
PACKAGING_REPO_URL = 'https://github.com/pypa/packaging.python.org.git'
PACKAGING_REPO_BRANCH = 'translation/source'
CHANGE_PERIOD = '30 days ago'

# Some locale directory names use script subtags instead of region codes.
# These explicit overrides take priority over the generic conversion.
RTD_CODE_TO_LOCALE_OVERRIDES: dict[str, str] = {'zh-cn': 'zh_Hans', 'zh-tw': 'zh_Hant'}
LOCALE_TO_RTD_CODE_OVERRIDES: dict[str, str] = {
    v: k for k, v in RTD_CODE_TO_LOCALE_OVERRIDES.items()
}

# Normalise locale/RTD codes that are aliases for the same language so they
# map to the canonical language code used elsewhere (e.g. in CPython devguide).
LOCALE_CODE_NORMALISATION: dict[str, str] = {
    # Hindi: packaging.python.org uses hi_IN / hi-in, CPython uses hi
    'hi_IN': 'hi',
    'hi-in': 'hi',
}


@dataclass(frozen=True)
class PackagingProjectData:
    language: Language
    completion: float
    change: float
    built: bool
    translated_name: str


def _rtd_code_to_locale(code: str) -> str:
    """Convert RTD language code (e.g. 'pt-br') to locale dir format ('pt_BR')."""
    if code in RTD_CODE_TO_LOCALE_OVERRIDES:
        return RTD_CODE_TO_LOCALE_OVERRIDES[code]
    parts = code.split('-')
    if len(parts) == 2:
        return f'{parts[0]}_{parts[1].upper()}'
    return code


def get_built_languages() -> dict[str, Language]:
    """Return a dict mapping locale directory name to Language for built languages."""
    built: dict[str, Language] = {}
    url: str | None = RTD_TRANSLATIONS_URL
    while url:
        resp = urllib3.request('GET', url)
        if resp.status != 200:
            logging.error('ReadTheDocs API returned status %d for %s', resp.status, url)
            break
        data = json.loads(resp.data)
        for result in data['results']:
            rtd_code = result['language']['code']
            language_name = result['language']['name']
            locale = _rtd_code_to_locale(rtd_code)
            built[locale] = Language(code=rtd_code, name=language_name)
        url = data.get('next')
    return built


def _po_completion(po_path: Path) -> float:
    if not po_path.exists():
        return 0.0
    try:
        po = polib.pofile(str(po_path))
        return po.percent_translated()
    except Exception:
        logging.exception('Failed to parse %s', po_path)
        return 0.0


def _get_locale_dirs(repo_path: Path) -> list[str]:
    locales_dir = repo_path / 'locales'
    if not locales_dir.exists():
        return []
    return [d.name for d in locales_dir.iterdir() if d.is_dir()]


def get_packaging_progress(clones_dir: Path) -> list[PackagingProjectData]:
    import translated_names

    repo_path = clones_dir / 'packaging.python.org'
    if not repo_path.exists():
        clone_repo = git.Repo.clone_from(
            PACKAGING_REPO_URL, repo_path, branch=PACKAGING_REPO_BRANCH
        )
    else:
        clone_repo = git.Repo(repo_path)
        clone_repo.git.fetch()
        clone_repo.git.switch(PACKAGING_REPO_BRANCH)
        clone_repo.git.pull()

    built_languages = get_built_languages()

    locales = _get_locale_dirs(repo_path)
    po_paths = {
        locale: repo_path / 'locales' / locale / 'LC_MESSAGES' / 'messages.po'
        for locale in locales
    }

    # Calculate current completions for all locales
    current_completions = {
        locale: _po_completion(po_paths[locale]) for locale in locales
    }

    # Find the 30-days-ago commit once and gather historical completions in a
    # single checkout round-trip (avoids N checkouts, one per locale).
    month_ago_completions: dict[str, float] = {}
    if any(current_completions.values()):
        try:
            old_commit = next(
                clone_repo.iter_commits('HEAD', max_count=1, before=CHANGE_PERIOD)
            )
        except StopIteration:
            pass
        else:
            clone_repo.git.checkout(old_commit.hexsha)
            for locale in locales:
                month_ago_completions[locale] = _po_completion(po_paths[locale])
            clone_repo.git.checkout(PACKAGING_REPO_BRANCH)

    results = []
    for locale in locales:
        completion = current_completions[locale]
        change = completion - month_ago_completions.get(locale, 0.0)

        # Determine language code and name.
        # Normalise known aliases (e.g. hi_IN → hi) before lookup.
        normalised_locale = LOCALE_CODE_NORMALISATION.get(locale, locale)
        if normalised_locale in built_languages:
            language = built_languages[normalised_locale]
        elif locale in built_languages:
            language = built_languages[locale]
        else:
            # Convert locale dir to RTD-style code, respecting explicit overrides.
            if normalised_locale in LOCALE_TO_RTD_CODE_OVERRIDES:
                rtd_code = LOCALE_TO_RTD_CODE_OVERRIDES[normalised_locale]
            elif locale in LOCALE_TO_RTD_CODE_OVERRIDES:
                rtd_code = LOCALE_TO_RTD_CODE_OVERRIDES[locale]
            else:
                parts = normalised_locale.split('_')
                if len(parts) == 2:
                    rtd_code = f'{parts[0]}-{parts[1].lower()}'
                else:
                    rtd_code = normalised_locale.lower()
            # Use babel for name; fall back to the code string itself.
            lang_name = translated_names.babel_autonym(rtd_code) or rtd_code
            language = Language(code=rtd_code, name=lang_name)

        translated_name = translated_names.babel_autonym(language.code) or ''

        results.append(
            PackagingProjectData(
                language=language,
                completion=completion,
                change=change,
                built=normalised_locale in built_languages or locale in built_languages,
                translated_name=translated_name,
            )
        )

    return results
