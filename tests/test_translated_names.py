import unittest
import support

from urllib3 import PoolManager

with support.import_scripts():
    import translated_names


class testBuildStatus(unittest.TestCase):
    def test_get_languages(self):
        result = {
            language: translated_name
            for language, translated_name in translated_names.get_languages(
                PoolManager()
            )
        }

        self.assertIn('en', result)
        self.assertIn('pl', result)
        self.assertIn('zh-cn', result)

        self.assertEqual(result.get('pl'), 'polski')
        self.assertEqual(result.get('zh-cn'), '简体中文')

    def test_babel_autonym(self):
        self.assertEqual(translated_names.babel_autonym('en'), 'English')
        self.assertEqual(translated_names.babel_autonym('ga'), 'Gaeilge')


if __name__ == '__main__':
    unittest.main()
