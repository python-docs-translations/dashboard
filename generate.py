# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "requests",
#     "docutils",
# ]
# ///
import subprocess
from collections.abc import Iterator
from datetime import datetime, timezone
from logging import info
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast, NamedTuple

from git import Repo
from jinja2 import Template

import contribute
import repositories
import build_status
import visitors
from completion import latest_branch_from_devguide, get_completion, TranslatorsData
from repositories import Language

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> Iterator['LanguageProjectData']:
    with TemporaryDirectory() as clones_dir:
        Repo.clone_from(
            'https://github.com/python/devguide.git',
            devguide_dir := Path(clones_dir, 'devguide'),
            depth=1,
        )
        Repo.clone_from(
            'https://github.com/python/cpython.git',
            Path(clones_dir, 'cpython'),
            depth=1,
            branch=latest_branch_from_devguide(devguide_dir),
        )
        subprocess.run(
            ['make', '-C', Path(clones_dir, 'cpython/Doc'), 'venv'], check=True
        )
        subprocess.run(
            ['make', '-C', Path(clones_dir, 'cpython/Doc'), 'gettext'], check=True
        )
        languages_built = dict(build_status.get_languages())
        for language, repo in repositories.get_languages_and_repos(devguide_dir):
            built = language.code in languages_built
            in_switcher = languages_built.get(language.code)
            tx = language.code in contribute.pulling_from_transifex
            contrib_link = contribute.get_contrib_link(language.code, repo)
            if not repo:
                yield LanguageProjectData(
                    language,
                    cast(str, repo),
                    0.0,
                    TranslatorsData(0, False),
                    0,
                    built,
                    in_switcher,
                    False,
                    None,
                )
                continue
            completion, translators_data = get_completion(clones_dir, repo)
            visitors_num = (
                visitors.get_number_of_visitors(language.code) if built else 0
            )
            yield LanguageProjectData(
                language,
                repo,
                completion,
                translators_data,
                visitors_num,
                built,
                in_switcher,
                tx,
                contrib_link,
            )


class LanguageProjectData(NamedTuple):
    language: Language
    repository: str
    completion: float
    translators: 'TranslatorsData'
    visitors: int
    built: bool
    in_switcher: bool | None
    uses_platform: bool
    contribution_link: str | None


if __name__ == '__main__':
    info(f'starting at {generation_time}')
    template = Template(Path('template.html.jinja').read_text())

    output = template.render(
        completion_progress=list(get_completion_progress()),
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
    )

    Path('index.html').write_text(output)
