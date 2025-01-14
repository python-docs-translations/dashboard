import re
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

from docutils import core
from docutils.nodes import table, row
from git import Repo


def get_languages_and_repos(
    devguide_dir: Path,
) -> Iterator[tuple[str, str, str | None]]:
    translating = devguide_dir.joinpath('documentation/translating.rst').read_text()
    doctree = core.publish_doctree(translating)

    for node in doctree.traverse(table):
        for row_node in node.traverse(row)[1:]:
            language = row_node[0].astext()
            repo = row_node[2].astext()
            language_match = re.match(r'(.*) \((.*)\)', language)
            if not language_match:
                raise ValueError(
                    f'Expected a language code in brackets in devguide table, found {language}'
                )
            language_name = language_match.group(1)
            language_code = language_match.group(2).lower().replace('_', '-')
            repo_match = re.match(':github:`GitHub <(.*)>`', repo)
            yield language_code, language_name, repo_match and repo_match.group(1)


if __name__ == '__main__':
    with TemporaryDirectory() as directory:
        Repo.clone_from('https://github.com/python/devguide.git', directory, depth=1)
        for item in get_languages_and_repos(Path(directory)):
            print(item)
