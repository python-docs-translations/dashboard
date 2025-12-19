from __future__ import annotations

import json
import concurrent.futures
import itertools
import logging
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile

from git import Repo
from jinja2 import Environment, FileSystemLoader
from urllib3 import PoolManager

import translated_names
import contribute
from completion import branches_from_peps, get_completion
from repositories import Language, get_languages_and_repos

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> Iterator[LanguageProjectData]:
    clones_dir = Path('clones')
    if not (devguide_dir := Path(clones_dir, 'devguide')).exists():
        Repo.clone_from('https://github.com/python/devguide.git', devguide_dir, depth=1)
    else:
        Repo(devguide_dir).git.pull()
    latest_branch = branches_from_peps()[0]
    if not (cpython_dir := Path(clones_dir, 'cpython')).exists():
        Repo.clone_from(
            'https://github.com/python/cpython.git',
            cpython_dir,
            depth=1,
            branch=latest_branch,
        )
    else:
        (cpython_repo := Repo(cpython_dir)).git.fetch()
        cpython_repo.git.switch(latest_branch)
        cpython_repo.git.pull()

    subprocess.run(['make', '-C', cpython_dir / 'Doc', 'clean'], check=True)
    subprocess.run(['make', '-C', cpython_dir / 'Doc', 'venv'], check=True)
    subprocess.run(['make', '-C', cpython_dir / 'Doc', 'gettext'], check=True)

    languages_built: dict[str, str] = {
        language: translated_name
        for language, translated_name in translated_names.get_languages(PoolManager())
    }

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.map(
            get_project_data,
            *zip(*get_languages_and_repos(devguide_dir)),
            itertools.repeat(languages_built),
            itertools.repeat(clones_dir),
        )


def get_project_data(
    language: Language,
    repo: str | None,
    languages_built: dict[str, str],
    clones_dir: str,
) -> LanguageProjectData:
    built = language.code in languages_built
    if repo:
        completion, branch, change = get_completion(clones_dir, repo)
    else:
        completion = 0.0
        change = 0.0
        branch = ''

    return LanguageProjectData(
        language,
        repo,
        branch,
        completion,
        change,
        built,
        translated_name=languages_built.get(language.code, ''),
        uses_platform=language.code in contribute.pulling_from_transifex,
        contribution_link=contribute.get_contrib_link(language.code, repo),
    )


@dataclass(frozen=True)
class LanguageProjectData:
    language: Language
    repository: str | None
    branch: str
    completion: float
    change: float
    built: bool
    translated_name: str
    uses_platform: bool
    contribution_link: str | None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f'starting at {generation_time}')
    Path('build').mkdir(parents=True, exist_ok=True)

    completion_progress = list(get_completion_progress())

    env = Environment(loader=FileSystemLoader('templates'))
    index = env.get_template('index.html.jinja').render(
        completion_progress=completion_progress,
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
    )
    copyfile('src/style.css', 'build/style.css')
    copyfile('src/logo.png', 'build/logo.png')
    Path('build/index.html').write_text(index)

    Path('build/index.json').write_text(
        json.dumps([asdict(project) for project in completion_progress], indent=2)
    )
