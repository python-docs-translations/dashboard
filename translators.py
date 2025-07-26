from collections.abc import Iterator
from pathlib import Path
from re import fullmatch, sub
from tempfile import TemporaryDirectory
from typing import Literal

from git import Repo
from polib import pofile


def _format_translator(translator: str) -> str:
    translator = translator.strip()
    return sub(r'<.*?>', '', translator).strip()


def get_number(path: Path) -> tuple[list, int]:
    from_po_headers = set(yield_from_headers(path))
    from_git_history = set(get_from_git_history(path))
    from_translators_file = set(get_from_translators_file(path))
    largest_set = max(from_po_headers, from_git_history, from_translators_file)
    return list(largest_set), len(largest_set)


def get_from_git_history(path: Path) -> list[str]:
    raw_lines = Repo(path).git.shortlog('-s', 'HEAD').splitlines()
    return [_format_translator(line.split('\t', 1)[-1]) for line in raw_lines]


def yield_from_headers(path: Path) -> Iterator[str]:
    for file in path.rglob('*.po'):
        try:
            header = pofile(file).header.splitlines()
        except IOError:
            continue
        if 'Translators:' not in header:
            continue
        for translator_record in header[header.index('Translators:') + 1 :]:
            try:
                translator, _year = translator_record.split(', ')
            except ValueError:
                translator = translator_record
            if translator.strip() == 'Transifex Bot <>':
                continue
            yield _format_translator(translator)


def get_from_translators_file(path: Path) -> list[str]:
    if not (file := path.joinpath('TRANSLATORS')).exists():
        return []
    return list(
        _format_translator(line)
        for line in file.read_text().splitlines()
        if line != 'Translators'
        and not fullmatch(r'-*', line)
        and not line.startswith('# ')
    )


def get_link(clone_path: Path, repo: str, branch: str) -> str | Literal[False]:
    return (
        clone_path.joinpath('TRANSLATORS').exists()
        and f'https://github.com/{repo}/blob/{branch}/TRANSLATORS'
    )


if __name__ == '__main__':
    for lang, branch in (
        ('es', '3.13'),
        ('hu', '3.6'),
        ('pl', '3.13'),
        ('zh-tw', '3.13'),
        ('id', '3.9'),
        ('fr', '3.13'),
        ('hu', '3.6'),
    ):
        with TemporaryDirectory() as directory:
            Repo.clone_from(
                f'https://github.com/python/python-docs-{lang}',
                directory,
                branch=branch,
            )
            from_headers = len(set(yield_from_headers(path := Path(directory))))
            from_git_history = get_from_git_history(path)
            from_translators_file = len(get_from_translators_file(path))
            print(
                f'{lang}: {from_headers=}, {from_git_history=}, {from_translators_file=}'
            )
