# /// script
# dependencies = [
#     "gitpython",
#     "potodo",
#     "jinja2",
#     "sphinx",
#     "blurb",
# ]
#
# [tool.uv.sources]
# potodo = { git = "https://git.afpy.org/maciek/potodo", branch = "pot" }
# ///
from datetime import datetime, timezone
from pathlib import Path
from shutil import rmtree
from subprocess import run
from tempfile import TemporaryDirectory
from git import Repo, GitCommandError
from potodo.potodo import merge_and_scan_path
from jinja2 import Template

completion_progress = []
generation_time = datetime.now(timezone.utc)

with TemporaryDirectory() as clones_dir:
    Repo.clone_from(f'https://github.com/python/cpython.git', Path(clones_dir, 'cpython'), depth=1, branch='3.13')
    run(['make', '-C', Path(clones_dir, 'cpython/Doc'), 'gettext'], check=True)
    for language in ('es', 'fr', 'id', 'it', 'ja', 'ko', 'pl', 'pt-br', 'tr', 'uk', 'zh-cn', 'zh-tw'):
        clone_path = Path(clones_dir, language)
        for branch in ('3.13', '3.12', '3.11', '3.10', '3.9'):
            try:
                Repo.clone_from(f'https://github.com/python/python-docs-{language}.git', clone_path, depth=1, branch=branch)
            except GitCommandError:
                print(f'failed to clone {language} {branch}')
                continue
            try:
                with TemporaryDirectory() as tmpdir:
                    completion = merge_and_scan_path(clone_path, pot_path=Path(clones_dir, 'cpython/Doc/build/gettext'), tmpdir=Path(tmpdir), hide_reserved=False, api_url='').completion
            except OSError as e:
                print(f'failed to scan {language} {branch}: {e}')
                rmtree(clone_path)
                continue
            else:
                break
        completion_progress.append((language, completion))
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
<tr><th>language</th><th>completion</th></tr>
</thead>
<tbody>
{% for language, completion in completion_progress | sort(attribute=1) | reverse %}
<tr>
  <td data-label="language">{{ language }}</td>
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
