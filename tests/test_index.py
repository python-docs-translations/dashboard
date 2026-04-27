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
        env.get_template('index.html.jinja').render(
            completion_progress=[language_project_data],
            packaging_progress=[packaging_project_data],
            generation_time=datetime.now(),
            duration=100,
        )


if __name__ == '__main__':
    unittest.main()
