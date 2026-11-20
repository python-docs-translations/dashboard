import unittest

import support
import urllib3

with support.import_scripts():
    import contribute


class testContributeLink(unittest.TestCase):
    def test_get_contrib_link(self):
        for code, repo, expected in (
            (
                'en',
                None,
                'https://devguide.python.org/documentation/translations/translating/',
            ),
            ('pl', None, 'https://explore.transifex.com/python-doc/python-newest/'),
            ('ar', 'python/python-docs-ar', 'https://github.com/python/python-docs-ar'),
        ):
            for branch in ('3.12', '3.14', '3.15', 'main', 'master'):
                with self.subTest(code=code, repo=repo, branch=branch):
                    self.assertEqual(
                        contribute.get_contrib_link(code, repo, branch), expected
                    )

    def test_custom_contrib_links(self):
        expected_links = {
            'zh-tw': 'https://github.com/python/python-docs-zh-tw/blob/{branch}/README.rst#id2',
            'id': 'https://github.com/python/python-docs-id/blob/{branch}/README.md#berkontribusi-untuk-menerjemahkan',
            'fr': 'https://git.afpy.org/AFPy/python-docs-fr/src/branch/{branch}/CONTRIBUTING.rst',
            'tr': 'https://github.com/python/python-docs-tr/blob/{branch}/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak',
            'el': 'https://github.com/python/python-docs-el/blob/{branch}/CONTRIBUTING.md',
            'es': 'https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html',
        }
        for code, expected in expected_links.items():
            for branch in ('3.12', '3.14', '3.15', 'main', 'master'):
                with self.subTest(code=code, branch=branch):
                    self.assertEqual(
                        contribute.get_contrib_link(code, None, branch),
                        expected.format(branch=branch),
                    )

    def test_links_are_valid(self):
        http = urllib3.PoolManager(
            timeout=1.0, retries=urllib3.Retry(total=3, read=False)
        )
        for lang, link in contribute.custom_contributing_links.items():
            link = link.format(branch='3.12' if lang == 'tr' else '3.14')
            with self.subTest(lang=lang, link=link):
                try:
                    response = http.request('HEAD', link)
                except urllib3.exceptions.ReadTimeoutError:
                    self.skipTest(f'{link}: read timeout, skipping slow server')
                self.assertTrue(
                    200 <= response.status < 400, f'{link} returned {response.status}'
                )


if __name__ == '__main__':
    unittest.main()
