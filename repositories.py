import pathlib
import re
from typing import Generator, Optional

from docutils import core
from docutils.nodes import table, row


def get_languages_and_repos(devguide_dir: pathlib.Path) -> Generator[tuple[str, Optional[str]], None, None]:
    translating = devguide_dir.joinpath('documentation/translating.rst').read_text()
    doctree = core.publish_doctree(translating)

    for node in doctree.traverse(table):
        for row_node in node.traverse(row)[1:]:
            language = row_node[0].astext()
            repo = row_node[2].astext()
            language_code = re.match(r'.* \((.*)\)', language).group(1).lower().replace('_', '-')
            repo_match = re.match(':github:`GitHub <(.*)>`', repo)
            yield language_code, repo_match and repo_match.group(1)
