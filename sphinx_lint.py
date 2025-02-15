from collections.abc import Iterator
from pathlib import Path

from sphinxlint import check_file, checkers


def errors(clones_dir: str, repo: str) -> Iterator[int]:
    for path in Path(clones_dir, repo).rglob('*.po'):
        yield len(
            check_file(
                path.as_posix(),
                [c for c in checkers.all_checkers.values() if c.enabled],
            )
        )
