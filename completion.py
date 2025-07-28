import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import git
from potodo import potodo

import translators


@cache
def branches_from_devguide(devguide_dir: Path) -> list[str]:
    p = devguide_dir.joinpath('include/release-cycle.json')
    data = json.loads(p.read_text())
    return [
        branch
        for branch in data
        if data[branch]['status'] in ('bugfix', 'security', 'prerelease')
    ]


def get_completion(
    clones_dir: str, repo: str
) -> tuple[float, 'TranslatorsData', str, float]:
    clone_path = Path(clones_dir, 'translations', repo)
    for branch in branches_from_devguide(Path(clones_dir, 'devguide')) + [
        'master',
        'main',
    ]:
        try:
            clone_repo = git.Repo.clone_from(
                f'https://github.com/{repo}.git', clone_path, branch=branch
            )
        except git.GitCommandError:
            print(f'failed to clone {repo} {branch}')
            translators_data = TranslatorsData(0, False)
            branch = ''
            continue
        else:
            translators_number = translators.get_number(clone_path)
            translators_link = translators.get_link(clone_path, repo, branch)
            translators_data = TranslatorsData(translators_number, translators_link)
            break
    path_for_merge = Path(clones_dir, 'rebased_translations', repo)
    completion = potodo.merge_and_scan_path(
        clone_path,
        pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'),
        merge_path=path_for_merge,
        hide_reserved=False,
        api_url='',
    ).completion

    if completion:
        # Fetch commit from before 30 days ago and checkout
        try:
            commit = next(
                clone_repo.iter_commits('HEAD', max_count=1, before='30 days ago')
            )
        except StopIteration:
            month_ago_completion = 0.0
        else:
            clone_repo.git.checkout(commit.hexsha)
            with TemporaryDirectory() as tmpdir:
                month_ago_completion = potodo.merge_and_scan_path(
                    clone_path,
                    pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'),
                    merge_path=Path(tmpdir),
                    hide_reserved=False,
                    api_url='',
                ).completion
            clone_repo.git.checkout(branch)  # restore the original state
    else:
        month_ago_completion = 0.0

    change = completion - month_ago_completion

    return completion, translators_data, branch, change


@dataclass(frozen=True)
class TranslatorsData:
    number: int
    link: str | Literal[False]
