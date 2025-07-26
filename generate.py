import json
import concurrent.futures
import itertools
import logging
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict
from pathlib import Path

from git import Repo
from jinja2 import Environment, FileSystemLoader
from urllib3 import PoolManager

import build_status
import contribute
from completion import branches_from_devguide, get_completion, TranslatorsData
from counts import get_counts
from repositories import Language, get_languages_and_repos

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> Iterator['LanguageProjectData']:
    clones_dir = Path('clones')
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

    languages_built: Dict[str, Dict[str, Any]] = {
        code: {'in_switcher': in_switcher, 'translated_name': translated_name}
        for code, translated_name, in_switcher in build_status.get_languages(
            PoolManager()
        )
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
    languages_built: Dict[str, Dict[str, Any]],
    clones_dir: str,
) -> 'LanguageProjectData':
    built = language.code in languages_built
    if repo:
        completion, translators_data, branch, change = get_completion(clones_dir, repo)
    else:
        completion = 0.0
        translators_data = TranslatorsData(0, [], False)
        change = 0.0
        branch = ''

    language_data = languages_built.get(language.code, {})
    translated_name = language_data.get('translated_name', '')
    in_switcher = language_data.get('in_switcher', False)

    return LanguageProjectData(
        language,
        repo,
        branch,
        completion,
        change,
        translators_data,
        built,
        translated_name=translated_name,
        in_switcher=in_switcher,
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
    translators: TranslatorsData
    built: bool
    translated_name: str
    in_switcher: bool | None
    uses_platform: bool
    contribution_link: str | None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f'starting at {generation_time}')
    Path('build').mkdir(parents=True, exist_ok=True)

    completion_progress = list(get_completion_progress())
    counts = get_counts(Path('clones', 'cpython', 'Doc', 'build', 'gettext'))

    env = Environment(loader=FileSystemLoader('templates'))
    index = env.get_template('index.html.jinja').render(
        completion_progress=completion_progress,
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
        counts=counts,
    )

    chart = env.get_template('chart.html.jinja').render(
        completion_progress=completion_progress,
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
        counts=counts,
    )

    lang_template = env.get_template('language.html.jinja')
    for project in completion_progress:
        code = project.language.code
        html = lang_template.render(project=project)
        Path(f'build/{code}.html').write_text(html)

    Path('build/style.css').write_bytes(Path('src/style.css').read_bytes())
    Path('build/logo.png').write_bytes(Path('src/logo.png').read_bytes())
    Path('build/index.html').write_text(index)
    Path('build/chart.html').write_text(chart)

    Path('build/index.json').write_text(
        json.dumps([asdict(project) for project in completion_progress], indent=2)
    )
