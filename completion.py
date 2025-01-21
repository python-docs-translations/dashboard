import json
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, NamedTuple

import git
from potodo import potodo

import translators


@cache
def latest_branch_from_devguide(devguide_dir: Path) -> str:
    p = devguide_dir.joinpath('include/release-cycle.json')
    for branch in (data := json.loads(p.read_text())):
        if data[branch]['status'] in ('bugfix', 'security'):
            return branch
    raise ValueError(f'Supported release not found in {p}')


def iterate_branches(latest: str) -> Iterator[str]:
    yield latest
    major, minor = latest.split('.')
    while int(minor) > 6:  # hu has 3.6 branch, hi has 3.7
        minor = str(int(minor) - 1)
        yield f'{major}.{minor}'
    yield 'master'


def get_completion(clones_dir: str, repo: str) -> tuple[float, 'TranslatorsData']:
    clone_path = Path(clones_dir, repo)
    for branch in iterate_branches(
        latest_branch_from_devguide(Path(clones_dir, 'devguide'))
    ):
        try:
            git.Repo.clone_from(
                f'https://github.com/{repo}.git', clone_path, branch=branch
            )
        except git.GitCommandError:
            print(f'failed to clone {repo} {branch}')
            translators_data = TranslatorsData(0, False)
            continue
        else:
            translators_number = translators.get_number(clone_path)
            translators_link = translators.get_link(clone_path, repo, branch)
            translators_data = TranslatorsData(translators_number, translators_link)
            break
    with TemporaryDirectory() as tmpdir:
        completion = potodo.merge_and_scan_path(
            clone_path,
            pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'),
            merge_path=Path(tmpdir),
            hide_reserved=False,
            api_url='',
        ).completion
    return completion, translators_data


class TranslatorsData(NamedTuple):
    number: int
    link: str | Literal[False]


if __name__ == '__main__':
    for branch in iterate_branches('3.13'):
        print(branch)
