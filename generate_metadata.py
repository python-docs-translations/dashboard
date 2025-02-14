# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "gitpython",
#     "jinja2",
#     "sphinx",
#     "python-docs-theme",
#     "dacite",
# ]
# ///
import concurrent.futures
import itertools
import logging
import subprocess
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from json import loads
from pathlib import Path
from sys import argv
from tempfile import TemporaryDirectory

import dacite
import git
from git import Repo
from jinja2 import Template
from urllib3 import request

import build_warnings
from completion import branches_from_devguide
from generate import LanguageProjectData
from repositories import Language

generation_time = datetime.now(timezone.utc)


def get_projects_metadata(
    completion_progress: Sequence[LanguageProjectData],
) -> Iterator[int]:
    with TemporaryDirectory() as clones_dir:
        Repo.clone_from(
            'https://github.com/python/devguide.git',
            devguide_dir := Path(clones_dir, 'devguide'),
            depth=1,
        )
        latest_branch = branches_from_devguide(devguide_dir)[0]
        Repo.clone_from(
            'https://github.com/python/cpython.git',
            cpython_dir := Path(clones_dir, 'cpython'),
            depth=1,
            branch=latest_branch,
        )
        subprocess.run(['make', '-C', cpython_dir / 'Doc', 'venv'], check=True)
        subprocess.run(['make', '-C', cpython_dir / 'Doc', 'gettext'], check=True)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            return executor.map(
                get_metadata,
                *zip(
                    *map(get_language_repo_branch_and_completion, completion_progress)
                ),
                itertools.repeat(clones_dir),
            )


def get_metadata(
    language: Language,
    repo: str | None,
    branch: str | None,
    completion: float,
    clones_dir: str,
) -> int:
    if repo:
        clone_path = Path(clones_dir, repo)
        git.Repo.clone_from(f'https://github.com/{repo}.git', clone_path, branch=branch)
    return (
        repo and completion and build_warnings.number(clones_dir, repo, language.code)
    ) or 0


def get_language_repo_branch_and_completion(
    project: LanguageProjectData,
) -> tuple[Language, str | None, str | None, float]:
    return project.language, project.repository, project.branch, project.completion


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f'starting at {generation_time}')
    template = Template(Path('metadata.html.jinja').read_text())
    if (index_path := Path('index.json')).exists():
        index_json = loads(Path('index.json').read_text())
    else:
        index_json = request('GET', argv[1]).json()

    completion_progress = [
        dacite.from_dict(LanguageProjectData, project) for project in index_json
    ]

    output = template.render(
        metadata=zip(completion_progress, get_projects_metadata(completion_progress)),
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
    )

    Path('metadata.html').write_text(output)
