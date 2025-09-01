import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from docutils import core
from docutils.nodes import table, row


def get_languages_and_repos(
    devguide_dir: Path,
) -> Iterator[tuple['Language', str | None]]:
    translating = devguide_dir.joinpath(
        'documentation/translations/translating.rst'
    ).read_text()
    doctree = core.publish_doctree(
        translating,
        settings_overrides={'report_level': 5},
        # docutils errors on Sphinx directives, but this does not matter for us
    )

    for node in doctree.findall(table):
        for row_node in list(node.findall(row))[1:]:
            language = row_node[0].astext()
            repo = row_node[2].astext()
            language_match = re.match(r'(.*) \((.*)\)', language)
            if not language_match:
                raise ValueError(
                    f'Expected a language code in brackets in devguide table, found {language}'
                )
            language_name = language_match.group(1)
            language_code = language_match.group(2).lower().replace('_', '-')
            repo_match = re.search(':github:`.* <(.*)>`', repo)
            yield (
                Language(language_code, language_name),
                repo_match and repo_match.group(1),
            )


@dataclass(frozen=True)
class Language:
    code: str
    name: str
