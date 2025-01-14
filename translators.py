from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from git import Repo
from polib import pofile


def get_number(path: Path) -> int:
    from_headers = len(set(yield_from_headers(path)))
    from_git_history = get_number_from_git_history(path)
    return max(from_headers, from_git_history)


def get_number_from_git_history(path: Path) -> int:
    return len(Repo(path).git.shortlog('-s', 'HEAD').splitlines())


def yield_from_headers(path: Path) -> Iterator[str]:
    for file in path.rglob('*.po'):
        try:
            header = pofile(file).header.splitlines()  # type: ignore[call-overload]  # https://github.com/python/typeshed/pull/13396
        except IOError:
            continue
        if 'Translators:' not in header:
            continue
        for translator_record in header[header.index('Translators:') + 1 :]:
            try:
                translator, _year = translator_record.split(', ')
            except ValueError:
                yield translator_record
            else:
                yield translator


def get_link(clone_path: Path, repo: str, branch: str) -> str | Literal[False]:
    return (
        clone_path.joinpath('TRANSLATORS').exists()
        and f'https://github.com/{repo}/blob/{branch}/TRANSLATORS'
    )
