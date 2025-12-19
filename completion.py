import json
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

import git
import urllib3
from potodo import potodo
from potodo.arguments_handling import Filters


@cache
def branches_from_peps() -> list[str]:
    resp = urllib3.request('GET', 'https://peps.python.org/api/release-cycle.json')
    data = json.loads(resp.data)
    return [
        branch
        for branch, metadata in data.items()
        if metadata['status'] in ('prerelease', 'bugfix', 'security')
    ]


def get_completion(
    clones_dir: str, repo: str
) -> tuple[float, float, str, float, float]:
    clone_path = Path(clones_dir, 'translations', repo)
    for branch in branches_from_peps() + ['master', 'main']:
        try:
            if not clone_path.exists():
                clone_repo = git.Repo.clone_from(
                    f'https://github.com/{repo}.git', clone_path, branch=branch
                )
            else:
                (clone_repo := git.Repo(clone_path)).git.fetch()
                clone_repo.git.switch(branch)
                clone_repo.git.pull()
        except git.GitCommandError:
            print(f'failure: {branch} {repo}: clone or switch, continuing')
            branch = ''
            continue
        else:
            print(f'success: {branch} {repo}: clone or switch')
            break
    path_for_merge = Path(clones_dir, 'rebased_translations', repo)
    project = potodo.merge_and_scan_paths(
        [clone_path],
        pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'),
        merge_path=path_for_merge,
        api_url='',
    )
    completion = project.completion
    project.filter(
        filters=Filters(False, True, 0, 100, False, False),
        exclude=['**/*', '!bugs.po', '!tutorial/', '!library/functions.po'],
    )
    core_completion = project.completion

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
                project = potodo.merge_and_scan_paths(
                    [clone_path],
                    pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'),
                    merge_path=Path(tmpdir),
                    api_url='',
                )
                month_ago_completion = project.completion
                project.filter(
                    filters=Filters(False, True, 0, 100, False, False),
                    exclude=['**/*', '!bugs.po', '!tutorial/', '!library/functions.po'],
                )
                month_ago_core_completion = project.completion
            clone_repo.git.checkout(branch)  # restore the original state
    else:
        month_ago_completion = 0.0
        month_ago_core_completion = 0.0

    change = completion - month_ago_completion
    core_change = core_completion - month_ago_core_completion

    return core_completion, completion, branch, core_change, change
