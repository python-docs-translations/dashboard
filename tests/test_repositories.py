import unittest
import support
import tempfile
import shutil

from pathlib import Path
from git import Repo

with support.import_scripts():
    import repositories
    from repositories import Language


class testRepositories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.test_repo_path = Path(cls.tempdir) / 'devguide'
        cls.test_repo = Repo.clone_from(
            'https://github.com/python/devguide',
            cls.test_repo_path,
            branch='main',
            depth=1,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def test_get_languages_and_repos(self):
        result = list(repositories.get_languages_and_repos(self.test_repo_path))

        for entry in result:
            info, repo = entry
            self.assertIsInstance(info, Language)

        self.assertIn(
            (Language(code='tr', name='Turkish'), 'python/python-docs-tr'), result
        )
        self.assertIn(
            (Language(code='es', name='Spanish'), 'python/python-docs-es'), result
        )
        self.assertIn(
            (Language(code='pl', name='Polish'), 'python/python-docs-pl'), result
        )
        self.assertIn(
            (
                Language(code='zh-tw', name='Traditional Chinese'),
                'python/python-docs-zh-tw',
            ),
            result,
        )
        self.assertIn(
            (Language(code='it', name='Italian'), 'python/python-docs-it'), result
        )

        self.assertGreater(len(result), 23 - 1)
