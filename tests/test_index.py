import unittest
from dataclasses import replace
from datetime import datetime
import support

from jinja2 import Environment, FileSystemLoader

with support.import_scripts():
    import generate
    import repositories


class testIndex(unittest.TestCase):
    def test_renders(self):
        env = Environment(loader=FileSystemLoader('templates'))
        language_project_data = generate.LanguageProjectData(
            language=repositories.Language('pl', 'Polish'),
            repository='python-docs-pl',
            branch='3.14',
            core_completion=100,
            completion=50,
            core_change=1,
            change=2,
            built=True,
            translated_name='Polish',
            contribution_link='https://example.com',
        )
        index = env.get_template('index.html.jinja').render(
            completion_progress=[language_project_data],
            python_version='3.15',
            release_cycle_status='prerelease',
            generation_time=datetime.now(),
            duration=100,
        )
        self.assertIn(
            'Measured against the Python 3.15 documentation (prerelease).', index
        )

    def test_orders_by_completion_score(self):
        env = Environment(loader=FileSystemLoader('templates'))
        language_project_data = generate.LanguageProjectData(
            language=repositories.Language('pl', 'Polish'),
            repository='python-docs-pl',
            branch='3.14',
            core_completion=100,
            completion=0,
            core_change=1,
            change=2,
            built=True,
            translated_name='Polish',
            contribution_link='https://example.com',
        )
        higher_completion_score = replace(
            language_project_data,
            language=repositories.Language('de', 'German'),
            core_completion=60,
            completion=60,
        )

        index = env.get_template('index.html.jinja').render(
            completion_progress=[language_project_data, higher_completion_score],
            python_version='3.15',
            release_cycle_status='prerelease',
            generation_time=datetime.now(),
            duration=100,
        )
        self.assertIn(
            '<option value="completion-score" selected>Completion score</option>', index
        )
        self.assertIn('<option value="completion">Overall completion</option>', index)
        self.assertIn('<option value="core-completion">Core completion</option>', index)
        self.assertIn('<option value="progress">Recent changes</option>', index)
        self.assertNotIn('<option value="audience">', index)
        self.assertIn('data-completion-score="100"', index)
        self.assertIn('data-core-completion="100"', index)
        self.assertIn('data-progress="2"', index)
        self.assertIn("document.querySelector('#languageContainer > .row')", index)
        self.assertIn("const sortStorageKey = 'dashboard-sort-by'", index)
        self.assertIn('localStorage.getItem(sortStorageKey)', index)
        self.assertIn('localStorage.setItem(sortStorageKey, this.value)', index)

        self.assertLess(index.index('German'), index.index('Polish'))


if __name__ == '__main__':
    unittest.main()
