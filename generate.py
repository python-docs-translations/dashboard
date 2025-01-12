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
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo
from jinja2 import Template

import repositories
import build_status
import visitors
from completion import branches_from_devguide, get_completion

completion_progress = []
generation_time = datetime.now(timezone.utc)

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
    subprocess.run(['make', '-C', Path(clones_dir, 'cpython/Doc'), 'venv'], check=True)
    subprocess.run(
        ['make', '-C', Path(clones_dir, 'cpython/Doc'), 'gettext'], check=True
    )
    languages_built = dict(build_status.get_languages())
    for language, repo in repositories.get_languages_and_repos(devguide_dir):
        if repo:
            completion_number, translators_number = get_completion(clones_dir, repo)
            visitors_number = visitors.get_number_of_visitors(language)
        else:
            completion_number, translators_number, visitors_number = 0.0, 0, 0
        completion_progress.append(
            (
                language,
                repo,
                completion_number,
                translators_number,
                visitors_number,
                language in languages_built,  # built on docs.python.org
                languages_built.get(language),  # in switcher
            )
        )
        print(completion_progress[-1])

template = Template(Path('template.html').read_text())

output = template.render(
    completion_progress=completion_progress, generation_time=generation_time
)

Path('index.html').write_text(output)
