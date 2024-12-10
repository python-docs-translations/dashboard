import tempfile
import pathlib
import re
from typing import Generator, Optional

import git
from docutils import core
from docutils.nodes import table, row

def get_languages_and_repos() -> Generator[tuple[str, Optional[str]], None, None]:
    with tempfile.TemporaryDirectory() as clone_path:
        git.Repo.clone_from(f'https://github.com/python/devguide.git', clone_path, depth=1)
        translating = pathlib.Path(clone_path, 'documentation/translating.rst').read_text()
    doctree = core.publish_doctree(translating)

    for node in doctree.traverse(table):
        for row_node in node.traverse(row)[1:]:
            language = row_node[0].astext()
            repo = row_node[2].astext()
            language_code = re.match(r'.* \((.*)\)', language).group(1).lower().replace('_', '-')
            repo_match = re.match(':github:`GitHub <(.*)>`', repo)
            yield language_code, repo_match and repo_match.group(1)
