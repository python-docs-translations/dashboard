import json
import concurrent.futures
import itertools
import logging
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from git import Repo
from jinja2 import Template
from urllib3 import PoolManager

import build_status
import contribute
from completion import branches_from_devguide, get_stats, TranslatorsData
from repositories import Language, get_languages_and_repos
from word_count import get_word_count

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
    languages_built = dict(build_status.get_languages(PoolManager()))

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
    languages_built: dict[str, bool],
    clones_dir: str,
) -> 'LanguageProjectData':
    built = language.code in languages_built
    if repo:
        stats, translators_data, branch, change = get_stats(clones_dir, repo)
    else:
        stats = SimpleNamespace(completion=0.0)
        translators_data = TranslatorsData(0, False)
        change = 0.0
        branch = ''
    return LanguageProjectData(
        language,
        repo,
        branch,
        stats.completion,
        change,
        translators_data,
        built,
        in_switcher=languages_built.get(language.code),
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
    in_switcher: bool | None
    uses_platform: bool
    contribution_link: str | None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f'starting at {generation_time}')
    template = Template(Path('template.html.jinja').read_text())

    output = template.render(
        completion_progress=(completion_progress := list(get_completion_progress())),
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
        word_count=get_word_count(Path('clones', 'cpython', 'Doc', 'build', 'gettext')),
    )

    Path('index.html').write_text(output)
    Path('index.json').write_text(
        json.dumps(completion_progress, indent=2, default=asdict)
    )
