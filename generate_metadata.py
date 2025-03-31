# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "sphinx",
#     "python-docs-theme",
#     "dacite",
#     "sphinx-lint",
# ]
# ///
import concurrent.futures
import itertools
import logging
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from json import loads
from pathlib import Path
from sys import argv

import dacite
from git import Repo
from jinja2 import Template
from urllib3 import request

import build_warnings
import sphinx_lint
from generate import LanguageProjectData
from repositories import Language

generation_time = datetime.now(timezone.utc)


def get_projects_metadata(
    completion_progress: Sequence[LanguageProjectData],
) -> Iterator[tuple[int, int, datetime | None]]:
    with concurrent.futures.ProcessPoolExecutor() as executor:
        return executor.map(
            get_metadata,
            *zip(*map(get_language_repo_and_completion, completion_progress)),
            itertools.repeat(Path('clones')),
        )


def get_metadata(
    language: Language, repo: str | None, completion: float, clones_dir: str
) -> tuple[int, int, datetime | None]:
    if not repo or not (repo_path := Path(clones_dir, 'translations', repo)).exists():
        return 0, 0, None
    (clone_repo := Repo(repo_path)).git.checkout()
    latest_commit = clone_repo.head.commit.committed_datetime
    if not completion:
        return 0, 0, latest_commit
    return (
        build_warnings.number(clones_dir, repo, language.code),
        sphinx_lint.store_and_count_failures(clones_dir, repo, language.code),
        latest_commit,
    )


def get_language_repo_and_completion(
    project: LanguageProjectData,
) -> tuple[Language, str | None, float]:
    return project.language, project.repository, project.completion


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
