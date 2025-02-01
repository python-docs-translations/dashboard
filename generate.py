# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "requests",
#     "docutils",
#     "sphinx",
#     "python-docs-theme",
# ]
# ///
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from logging import info
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo
from jinja2 import Template

import build_warnings
import build_status
import contribute
from visitors import get_number_of_visitors
from completion import branches_from_devguide, get_completion, TranslatorsData
from repositories import Language, get_languages_and_repos

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> Iterator['LanguageProjectData']:
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
        languages_built = dict(build_status.get_languages())
        for language, repo in get_languages_and_repos(devguide_dir):
            built = language.code in languages_built
            if repo:
                completion, translators_data = get_completion(clones_dir, repo)
                visitors_num = get_number_of_visitors(language.code) if built else 0
                issues = build_warnings.number(clones_dir, repo, language.code)
            else:
                completion = 0.0
                translators_data = TranslatorsData(0, False)
                visitors_num = 0
                issues = 0
            yield LanguageProjectData(
                language,
                repo,
                completion,
                translators_data,
                visitors_num,
                issues,
                built,
                in_switcher=languages_built.get(language.code),
                uses_platform=language.code in contribute.pulling_from_transifex,
                contribution_link=contribute.get_contrib_link(language.code, repo),
            )


@dataclass(frozen=True)
class LanguageProjectData:
    language: Language
    repository: str | None
    completion: float
    translators: TranslatorsData
    visitors: int
    issues: int
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
