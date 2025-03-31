import os
from polib import pofile

def _count_words(pot) -> int:
    pot = pofile(pot)
    word_count = 0
    for entry in pot:
        word_count += len(entry.msgid.split())
    return word_count

def get_word_count(dir) -> int:
    total_word_count = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith('.pot'):
                pot = os.path.join(root, file)
                total_word_count += _count_words(pot)
    return total_word_count
