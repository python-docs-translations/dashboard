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
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast, Literal

from git import Repo
from jinja2 import Template

import contribute
import repositories
import build_status
import visitors
from completion import branches_from_devguide, get_completion

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> (
    Iterator[
        tuple[
            str,
            str,
            float,
            int,
            str | Literal[False],
            int,
            bool,
            bool | None,
            bool,
            str | Literal[False],
        ]
    ]
):
    with TemporaryDirectory() as clones_dir:
        Repo.clone_from(
            'https://github.com/python/devguide.git',
            devguide_dir := Path(clones_dir, 'devguide'),
            depth=1,
        )
        latest_branch = branches_from_devguide(devguide_dir)[0]
        Repo.clone_from(
            'https://github.com/python/cpython.git',
            Path(clones_dir, 'cpython'),
            depth=1,
            branch=latest_branch,
        )
        subprocess.run(
            ['make', '-C', Path(clones_dir, 'cpython/Doc'), 'venv'], check=True
        )
        subprocess.run(
            ['make', '-C', Path(clones_dir, 'cpython/Doc'), 'gettext'], check=True
        )
        languages_built = dict(build_status.get_languages())
        for lang, repo in repositories.get_languages_and_repos(devguide_dir):
            built = lang in languages_built
            in_switcher = languages_built.get(lang)
            tx = lang in contribute.pulling_from_transifex
            contrib_link = contribute.get_contrib_link(lang)
            if not repo:
                yield (
                    lang,
                    cast(str, repo),
                    0.0,
                    0,
                    False,
                    0,
                    built,
                    in_switcher,
                    False,
                    False,
                )
                continue
            completion, translators, translators_link = get_completion(clones_dir, repo)
            visitors_num = visitors.get_number_of_visitors(lang) if built else 0
            yield (
                lang,
                repo,
                completion,
                translators,
                translators_link,
                visitors_num,
                built,
                in_switcher,
                tx,
                contrib_link,
            )


if __name__ == '__main__':
    template = Template(Path('template.html.jinja').read_text())

    output = template.render(
        completion_progress=get_completion_progress(), generation_time=generation_time
    )

    Path('index.html').write_text(output)
