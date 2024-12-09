import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import git
from potodo import potodo


def get_completion(clones_dir: str, language: str) -> float:
    clone_path = Path(clones_dir, language)
    for branch in ('3.13', '3.12', '3.11', '3.10', '3.9'):
        try:
            git.Repo.clone_from(
                f'https://github.com/python/python-docs-{language}.git', clone_path, depth=1, branch=branch
            )
        except git.GitCommandError:
            print(f'failed to clone {language} {branch}')
            continue
        else:
            break
    with tempfile.TemporaryDirectory() as tmpdir:
        completion = potodo.merge_and_scan_path(
            clone_path, pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'), merge_path=Path(tmpdir), hide_reserved=False, api_url=''
        ).completion
    return completion
