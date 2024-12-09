# /// script
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "requests",
#     "humanize",
# ]
# ///
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from urllib.parse import urlencode

import humanize
import requests
from git import Repo, GitCommandError
from potodo.potodo import scan_path
from jinja2 import Template

import completion
import visitors

completion_progress = []
generation_time = datetime.now(timezone.utc)

with TemporaryDirectory() as tmpdir:
    for language in ('es', 'fr', 'id', 'it', 'ja', 'ko', 'pl', 'pt-br', 'tr', 'uk', 'zh-cn', 'zh-tw'):
        completion_number, branch = completion.get_completion_and_branch(tmpdir, language)
        visitors_number = visitors.get_number_of_visitors(language)
        completion_progress.append((language, completion_number, branch, visitors_number))
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
  <th>branch</th>
  <th>completion</th>
</tr>
</thead>
<tbody>
{% for language, completion, branch, visitors in completion_progress | sort(attribute=1) | reverse %}
<tr>
  <td data-label="language">
    <a href="https://github.com/python/python-docs-{{ language }}" target="_blank">
      {{ language }}
    </a>
  </td>
  <td data-label="visitors">
    <a href="https://https://plausible.io/docs.python.org?filters=((contains,page,(/{{ language }}/)))" target="_blank">
      {{ visitors }}
    </a>
  </td>
  <td data-label="branch">{{ branch }}</td>
  <td data-label="completion">
    <div class="progress-bar" style="width: {{ completion | round(2) }}%;">{{ completion | round(2) }}%</div>
  </td>
</tr>
{% endfor %}
</tbody>
</table>
<p>Last updated at {{ generation_time.strftime('%A, %d %B %Y, %X %Z') }}.</p>
<p>Note that the completion value is based on files available in language Git repository and <a href="https://github.com/m-aciek/pydocs-translation-dashboard/issues/2" target="_blank">may not include</a> e.g. resources which translation hasn't yet started.</p>
</body>
</html>
""")

output = template.render(completion_progress=completion_progress, generation_time=generation_time)

with open("index.html", "w") as file:
    file.write(output)
