import unittest
from datetime import datetime
import support

from jinja2 import Environment, FileSystemLoader

with support.import_scripts():
    import generate
    import repositories
    import packaging_completion


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
        packaging_project_data = packaging_completion.PackagingProjectData(
            language=repositories.Language('ja', 'Japanese'),
            completion=75.0,
            change=2.0,
            built=True,
            translated_name='日本語',
        )
        combined = generate.merge_progress(
            [language_project_data], [packaging_project_data]
        )
        env.get_template('index.html.jinja').render(
            combined_progress=combined, generation_time=datetime.now(), duration=100
        )

    def test_renders_combined_card(self):
        """A language present in both CPython and packaging data shares one card."""
        env = Environment(loader=FileSystemLoader('templates'))
        cpython_data = generate.LanguageProjectData(
            language=repositories.Language('ja', 'Japanese'),
            repository='python-docs-ja',
            branch='3.14',
            core_completion=90,
            completion=80,
            core_change=0,
            change=1,
            built=True,
            translated_name='日本語',
            contribution_link='https://example.com',
        )
        packaging_data = packaging_completion.PackagingProjectData(
            language=repositories.Language('ja', 'Japanese'),
            completion=75.0,
            change=2.0,
            built=True,
            translated_name='日本語',
        )
        combined = generate.merge_progress([cpython_data], [packaging_data])
        self.assertEqual(len(combined), 1)
        self.assertIsNotNone(combined[0].cpython)
        self.assertIsNotNone(combined[0].packaging)
        env.get_template('index.html.jinja').render(
            combined_progress=combined, generation_time=datetime.now(), duration=100
        )

    def test_hindi_normalisation(self):
        """hi-in packaging entry is merged onto the same card as hi CPython entry."""
        cpython_data = generate.LanguageProjectData(
            language=repositories.Language('hi', 'Hindi'),
            repository='python-docs-hi',
            branch='3.14',
            core_completion=20,
            completion=15,
            core_change=0,
            change=0,
            built=False,
            translated_name='हिन्दी',
            contribution_link='https://example.com',
        )
        packaging_data = packaging_completion.PackagingProjectData(
            language=repositories.Language('hi-in', 'Hindi (India)'),
            completion=10.0,
            change=0.0,
            built=False,
            translated_name='हिन्दी',
        )
        combined = generate.merge_progress([cpython_data], [packaging_data])
        self.assertEqual(len(combined), 1)
        self.assertIsNotNone(combined[0].cpython)
        self.assertIsNotNone(combined[0].packaging)


if __name__ == '__main__':
    unittest.main()
