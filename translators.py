from collections.abc import Generator
from pathlib import Path

from polib import pofile


def get_number_of_translators(path: Path) -> int:
    translators = set(_fetch_translators(path))
    return len(translators)


def _fetch_translators(path: Path) -> Generator[str, None, None]:
    for file in path.rglob('*.po'):
        try:
            header = pofile(file).header.splitlines()
        except IOError:
            continue
        if 'Translators:' not in header:
            continue
        for translator_record in header[header.index('Translators:') + 1:]:
            try:
                translator, _year = translator_record.split(', ')
            except ValueError:
                yield translator_record
            else:
                yield translator
