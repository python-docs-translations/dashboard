import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import support
from jinja2 import Environment, FileSystemLoader

with support.import_scripts():
    from generate_build_details import get_build_details
    from repositories import Language


class TestBuildDetails(unittest.TestCase):
    def test_pospell_uses_translation_branch_even_with_zero_completion(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch('generate_build_details.Repo') as repo,
            patch('generate_build_details.build_warnings.number', return_value=2),
            patch(
                'generate_build_details.sphinx_lint.store_and_count_failures',
                return_value=3,
            ),
            patch(
                'generate_build_details.pospell_check.store_and_count_failures',
                return_value=4,
            ) as pospell,
        ):
            Path(directory, 'translations', 'python/python-docs-pl').mkdir(parents=True)
            updated = datetime.now(UTC)
            repo.return_value.head.commit.committed_datetime = updated
            for completion in (0, 50):
                with self.subTest(completion=completion):
                    result = get_build_details(
                        Language('pl', 'Polish'),
                        'python/python-docs-pl',
                        completion,
                        '3.15',
                        directory,
                    )
                    self.assertEqual(
                        result, (2, 3, updated, 4) if completion else (0, 0, updated, 4)
                    )
                    pospell.assert_called_with('python/python-docs-pl', '3.15', 'pl')

    def test_missing_repository_has_no_pospell_result(self):
        with patch(
            'generate_build_details.pospell_check.store_and_count_failures'
        ) as fetch:
            self.assertEqual(
                get_build_details(Language('pl', 'Polish'), None, 0, '', ''),
                (0, 0, None, None),
            )
            fetch.assert_not_called()

    def test_template_links_available_reports_including_zero(self):
        env = Environment(loader=FileSystemLoader('templates'))
        for count in (None, 0, 12):
            with self.subTest(count=count):
                page = env.get_template('build-details.html.jinja').render(
                    build_details=[
                        (
                            {
                                'language': Language('fr', 'French'),
                                'repository': 'python/python-docs-fr',
                                'branch': '3.15',
                                'completion': 50,
                            },
                            (1, 2, datetime.now(UTC), count),
                        )
                    ],
                    generation_time=datetime.now(UTC),
                    duration=0,
                )
                self.assertIn('<th>pospell check</th>', page)
                if count is None:
                    self.assertIn('unavailable', page)
                    self.assertNotIn('href="warnings-pospell-fr.txt"', page)
                else:
                    self.assertIn(
                        f'<a href="warnings-pospell-fr.txt">{count}</a>', page
                    )
                self.assertIn('href="warnings-fr.txt">1</a>', page)
                self.assertIn('href="warnings-lint-fr.txt">2</a>', page)
