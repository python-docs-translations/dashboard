import unittest
import support

from urllib3 import PoolManager

with support.import_scripts():
    import build_status


class testBuildStatus(unittest.TestCase):
    def test_get_languages(self):
        result = {
            language: in_switcher
            for language, in_switcher in build_status.get_languages(PoolManager())
        }

        self.assertIn('en', result)
        self.assertIn('pl', result)
        self.assertIn('zh-cn', result)

        self.assertEqual(result.get('en'), True)
        self.assertEqual(result.get('pl'), True)


if __name__ == '__main__':
    unittest.main()
