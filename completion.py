import pathlib
import shutil

import git
from potodo import potodo


def get_completion_and_branch(tmpdir: str, language: str) -> tuple[float, str]:
    clone_path = pathlib.Path(tmpdir, language)
    for branch in ('3.13', '3.12', '3.11', '3.10', '3.9'):
        try:
            git.Repo.clone_from(f'https://github.com/python/python-docs-{language}.git', clone_path, depth=1, branch=branch)
        except git.GitCommandError:
            print(f'failed to clone {language} {branch}')
            continue
        try:
            completion = potodo.scan_path(clone_path, no_cache=True, hide_reserved=False, api_url='').completion
        except OSError:
            print(f'failed to scan {language} {branch}')
            shutil.rmtree(clone_path)
            continue
        else:
            break
    return completion, branch
