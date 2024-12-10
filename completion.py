from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

import git
from potodo import potodo
import requests

@cache
def branches_from_devguide() -> list[str]:
    r = requests.get(
        "https://raw.githubusercontent.com/"
        "python/devguide/main/include/release-cycle.json",
        timeout=10,
    )
    data = r.json()
    return [
        branch for branch in data if data[branch]["status"] in ("bugfix", "security")
    ]


def get_completion(clones_dir: str, repo: str) -> float:
    clone_path = Path(clones_dir, repo)
    for branch in branches_from_devguide() + ['master']:
        try:
            git.Repo.clone_from(
                f'https://github.com/{repo}.git', clone_path, depth=1, branch=branch
            )
        except git.GitCommandError:
            print(f'failed to clone {repo} {branch}')
            continue
        else:
            break
    with TemporaryDirectory() as tmpdir:
        completion = potodo.merge_and_scan_path(
            clone_path, pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'), merge_path=Path(tmpdir), hide_reserved=False, api_url=''
        ).completion
    return completion
