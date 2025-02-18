from collections.abc import Iterator
from itertools import chain
from pathlib import Path

from sphinxlint import check_file, checkers


def store_and_count_failures(clones_dir: str, repo: str, language_code: str) -> int:
    failed_checks = list(chain.from_iterable(yield_failures(clones_dir, repo)))
    filepath = Path(f'warnings-lint-{language_code}.txt')
    filepath.write_text('\n'.join([str(c) for c in failed_checks]))
    return len(failed_checks)


def yield_failures(clones_dir: str, repo: str) -> Iterator[str]:
    enabled_checkers = [c for c in checkers.all_checkers.values() if c.enabled]
    for path in Path(clones_dir, repo).rglob('*.po'):
        yield check_file(path.as_posix(), enabled_checkers)
