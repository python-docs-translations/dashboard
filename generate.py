# /// script
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "requests",
# ]
# ///
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo
from jinja2 import Template

import visitors
from completion import branches_from_devguide, get_completion

completion_progress = []
generation_time = datetime.now(timezone.utc)

with TemporaryDirectory() as clones_dir:
    Repo.clone_from(
        f'https://github.com/python/cpython.git', Path(clones_dir, 'cpython'), depth=1, branch=branches_from_devguide()[0]
    )
    subprocess.run(['make', '-C', Path(clones_dir, 'cpython/Doc'), 'venv'], check=True)
    subprocess.run(['make', '-C', Path(clones_dir, 'cpython/Doc'), 'gettext'], check=True)
    for language in ('es', 'fr', 'id', 'it', 'ja', 'ko', 'pl', 'pt-br', 'tr', 'uk', 'zh-cn', 'zh-tw'):
        completion_number = get_completion(clones_dir, language)
        visitors_number = visitors.get_number_of_visitors(language)
        completion_progress.append((language, completion_number, visitors_number))
        print(completion_progress[-1])

template = Template("""
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
  <th><a href="https://plausible.io/data-policy#how-we-count-unique-users-without-cookies">visitors<a/></th>
  <th>completion</th>
</tr>
</thead>
<tbody>
{% for language, completion, visitors in completion_progress | sort(attribute=1) | reverse %}
<tr>
  <td data-label="language">
    <a href="https://github.com/python/python-docs-{{ language }}" target="_blank">
      {{ language }}
    </a>
  </td>
  <td data-label="visitors">
    <a href="https://plausible.io/docs.python.org?filters=((contains,page,(/{{ language }}/)))" target="_blank">
      {{ '{:,}'.format(visitors) }}
    </a>
  </td>
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
""")

output = template.render(completion_progress=completion_progress, generation_time=generation_time)

with open("index.html", "w") as file:
    file.write(output)
