import re
from collections.abc import Iterator
from pathlib import Path

from docutils import core
from docutils.nodes import table, row


def get_languages_and_repos(devguide_dir: Path) -> Iterator[tuple[str, str | None]]:
    translating = devguide_dir.joinpath('documentation/translating.rst').read_text()
    doctree = core.publish_doctree(translating)

    for node in doctree.traverse(table):
        for row_node in node.traverse(row)[1:]:
            language = row_node[0].astext()
            repo = row_node[2].astext()
            language_match = re.match(r'.* \((.*)\)', language)
            if not language_match:
                raise ValueError(
                    f'Expected a language code in brackets in devguide table, found {language}'
                )
            language_code = language_match.group(1).lower().replace('_', '-')
            repo_match = re.match(':github:`GitHub <(.*)>`', repo)
            yield language_code, repo_match and repo_match.group(1)
