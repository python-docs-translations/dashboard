import unittest
import support
import tempfile
import shutil

from pathlib import Path
from git import Repo

with support.import_scripts():
    import translators

TRANSLATORS_BASIC = """
John Cleese
Graham Chapman
Terry Jones
Michael Palin
Terry Gilliam
"""

TRANSLATORS_TITLE_AND_COMMENTS = """
Translators
John Cleese
Graham Chapman
Terry Jones
# Also Translators
Michael Palin
Terry Gilliam
"""

TRANSLATORS_COMPLEX = """
Translators
John Cleese
-----


Graham Chapman
Graham Chapman
# I'm a line
Terry Jones
# # #
-
Michael Palin
Terry Gilliam
"""


class testTranslators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.test_repo_path = Path(cls.tempdir) / 'python-docs-pl'
        cls.test_repo = Repo.clone_from(
            'https://github.com/python/python-docs-pl',
            cls.test_repo_path,
            branch='3.14',
        )
        cls.test_repo.git.checkout('d242ceee48cfa6d70dbc0bc75f5043d1e6c5efeb')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def test_yield_from_headers(self):
        translators_list = set(translators.yield_from_headers(self.test_repo_path))
        self.assertEqual(len(translators_list), 25)

    def test_get_number_from_git_history(self):
        # ["   183\tGitHub Action's commit-build job", "    84\tGitHub Action's update-chart job", "     6\tGitHub Action's update-readme job", "  1342\tGitHub Action's update-translation job", '   174\tMaciej Olko', '     3\tStan U.', '    20\tStan Ulbrych', '     1\tciarbin', '     5\tm-aciek']
        self.assertEqual(
            translators.get_number_from_git_history(self.test_repo_path), 9
        )

    def test_get_translators_from_file(self):
        for i, file in enumerate(
            (TRANSLATORS_BASIC, TRANSLATORS_TITLE_AND_COMMENTS, TRANSLATORS_COMPLEX)
        ):
            with self.subTest(i=i, file=file):
                folder = Path(self.tempdir) / f'folder-{i}'
                folder.mkdir()
                (folder / 'TRANSLATORS').write_text(file)

                result = translators.get_from_translators_file(folder)
                self.assertEqual(len(result), 5)

        # No TRANSLATORS file
        result = translators.get_from_translators_file(Path(self.tempdir) / 'empty')
        self.assertEqual(result, set())

    def test_get_number(self):
        (self.test_repo_path / 'TRANSLATORS').write_text(TRANSLATORS_COMPLEX)

        result = translators.get_number(self.test_repo_path)
        self.assertEqual(result, 25)


if __name__ == '__main__':
    unittest.main()
