import unittest
import urllib3
import support

with support.import_scripts():
    import contribute


class testContributeLink(unittest.TestCase):
    def test_get_contrib_link(self):
        PULL_FROM_TX = 'https://explore.transifex.com/python-doc/python-newest/'
        DEVGUIDE = 'https://devguide.python.org/documentation/translations/translating/'

        for code, repo, expected in (
            ('en', None, DEVGUIDE),
            ('pl', None, PULL_FROM_TX),
            ('ar', 'python/python-docs-ar', 'https://github.com/python/python-docs-ar'),
            (
                'zh-tw',
                None,
                'https://github.com/python/python-docs-zh-tw/blob/3.13/README.rst#%E5%8F%83%E8%88%87%E7%BF%BB%E8%AD%AF',
            ),
            (
                'id',
                None,
                'https://github.com/python/python-docs-id/blob/3.14/README.md#berkontribusi-untuk-menerjemahkan',
            ),
        ):
            with self.subTest(code=code, repo=repo, expected=expected):
                self.assertEqual(contribute.get_contrib_link(code, repo), expected)

    def test_links_are_valid(self):
        http = urllib3.PoolManager()
        for lang, link in contribute.custom_contributing_links.items():
            with self.subTest(lang=lang):
                try:
                    r = http.request('HEAD', link, timeout=urllib3.Timeout(10.0))
                    self.assertTrue(
                        200 <= r.status < 400, f'{link} returned {r.status}'
                    )
                except Exception as e:
                    self.fail(f'{link}: {e}')


if __name__ == '__main__':
    unittest.main()
