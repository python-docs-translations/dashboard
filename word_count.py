from pathlib import Path

from polib import pofile


def _count(pot) -> tuple[int, int]:
    pot = pofile(pot)
    word_count = 0
    for entry in pot:
        word_count += len(entry.msgid.split())
    return len(pot), word_count


def get_counts(dir: Path) -> tuple[int, int]:
    total_string_count = 0
    total_word_count = 0
    for root, dirs, files in dir.walk():
        for file in files:
            if file.endswith('.pot'):
                pot = root.joinpath(root, file)
                strings, words = _count(pot)
                total_string_count += strings
                total_word_count += words
    return total_string_count, total_word_count
