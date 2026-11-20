import unittest

import support
import urllib3

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
                'https://github.com/python/python-docs-zh-tw/blob/3.14/README.rst#id2',
            ),
            (
                'id',
                None,
                'https://github.com/python/python-docs-id/blob/3.14/README.md#berkontribusi-untuk-menerjemahkan',
            ),
            (
                'fr',
                None,
                'https://git.afpy.org/AFPy/python-docs-fr/src/branch/3.14/CONTRIBUTING.rst',
            ),
            (
                'tr',
                None,
                'https://github.com/python/python-docs-tr/blob/3.14/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak',
            ),
            (
                'el',
                None,
                'https://github.com/python/python-docs-el/blob/3.14/CONTRIBUTING.md',
            ),
            (
                'es',
                None,
                'https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html',
            ),
        ):
            for branch in ('3.12', '3.14', '3.15', 'main', 'master'):
                with self.subTest(code=code, repo=repo, branch=branch):
                    self.assertEqual(
                        contribute.get_contrib_link(code, repo, branch),
                        expected.replace('/3.14/', f'/{branch}/'),
                    )

    def test_links_are_valid(self):
        http = urllib3.PoolManager()
        for lang, link in contribute.custom_contributing_links.items():
            link = link.format(branch='3.12' if lang == 'tr' else '3.14')
            with self.subTest(lang=lang):
                try:
                    r = http.request('HEAD', link, timeout=urllib3.Timeout(10.0))
                    self.assertTrue(
                        200 <= r.status < 400, f'{link} returned {r.status}'
                    )
                except urllib3.exceptions.MaxRetryError as e:
                    if isinstance(e.reason, urllib3.exceptions.ReadTimeoutError):
                        self.skipTest(f'{link}: read timeout, skipping slow server')
                    self.fail(f'{link}: {e}')
                except urllib3.exceptions.HTTPError as e:
                    self.fail(f'{link}: {e}')


if __name__ == '__main__':
    unittest.main()
