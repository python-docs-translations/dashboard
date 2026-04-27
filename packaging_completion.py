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
        # Both translated_entries() and untranslated_entries() exclude fuzzy
        # entries, so fuzzy strings are omitted from both numerator and
        # denominator and don't inflate the reported completion.
        translated = len(po.translated_entries())
        total = translated + len(po.untranslated_entries())
        if total == 0:
            return 0.0
        return translated * 100.0 / total
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

    results = []
    for locale in _get_locale_dirs(repo_path):
        po_path = repo_path / 'locales' / locale / 'LC_MESSAGES' / 'messages.po'
        completion = _po_completion(po_path)

        # Determine language code and name
        if locale in built_languages:
            language = built_languages[locale]
        else:
            # Convert locale dir back to RTD-style code.
            # Check explicit overrides first (e.g. zh_Hans → zh-cn).
            if locale in LOCALE_TO_RTD_CODE_OVERRIDES:
                rtd_code = LOCALE_TO_RTD_CODE_OVERRIDES[locale]
            else:
                parts = locale.split('_')
                if len(parts) == 2:
                    rtd_code = f'{parts[0]}-{parts[1].lower()}'
                else:
                    rtd_code = locale.lower()
            language = Language(code=rtd_code, name=rtd_code)

        translated_name = translated_names.babel_autonym(language.code) or ''

        # Calculate change over last 30 days
        change = 0.0
        if completion:
            try:
                commit = next(
                    clone_repo.iter_commits('HEAD', max_count=1, before=CHANGE_PERIOD)
                )
            except StopIteration:
                pass
            else:
                clone_repo.git.checkout(commit.hexsha)
                month_ago_completion = _po_completion(po_path)
                clone_repo.git.checkout(PACKAGING_REPO_BRANCH)
                change = completion - month_ago_completion

        results.append(
            PackagingProjectData(
                language=language,
                completion=completion,
                change=change,
                built=locale in built_languages,
                translated_name=translated_name,
            )
        )

    return results
