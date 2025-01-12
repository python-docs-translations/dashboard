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
    languages_built = {
        language: in_switcher for language, in_switcher in build_status.get_languages()
    }
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

template = Template(
    """
<html lang="en">
<head>
  <title>Python Docs Translation Dashboard</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<h1>Python Docs Translation Dashboard</h1>
<table>
<thead>
<tr>
  <th>language</th>
  <th>build</th>
  <th><a href="https://plausible.io/data-policy#how-we-count-unique-users-without-cookies">visitors<a/></th>
  <th>translators</th>
  <th>completion</th>
</tr>
</thead>
<tbody>
{% for language, repo, completion, translators, visitors, build, in_switcher in completion_progress | sort(attribute='2,3') | reverse %}
<tr>
  {% if repo %}
  <td data-label="language">
    <a href="https://github.com/{{ repo }}" target="_blank">
      {{ language }}
    </a>
  </td>
  {% else %}
  <td data-label="language">{{ language }}</td>
  {% endif %}
  <td data-label="build">
    {% if build %}
      <a href="https://docs.python.org/{{ language }}/" target="_blank">✓ {% if in_switcher %}in switcher{% endif %}</a>
    {% else %}
      ✗
    {% endif %}
  </td>
  <td data-label="visitors">
    <a href="https://plausible.io/docs.python.org?filters=((contains,page,(/{{ language }}/)))" target="_blank">
      {{ '{:,}'.format(visitors) }}
    </a>
  </td>
  <td data-label="translators">{{ '{:,}'.format(translators) }}</td>
  <td data-label="completion">
    <div class="progress-bar" style="width: {{ completion | round(2) }}%;">{{ completion | round(2) }}%</div>
  </td>
</tr>
{% endfor %}
</tbody>
</table>
<p>Last updated at {{ generation_time.strftime('%A, %d %B %Y, %X %Z') }}.</p>
</body>
</html>
"""
)

output = template.render(
    completion_progress=completion_progress, generation_time=generation_time
)

with open('index.html', 'w') as file:
    file.write(output)
