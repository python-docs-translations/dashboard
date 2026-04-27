import unittest
import support

with support.import_scripts():
    from continents import get_language_continents


class TestGetLanguageContinents(unittest.TestCase):
    def test_single_continent(self):
        # Polish is only spoken in Europe
        self.assertEqual(get_language_continents('pl'), ['Europe'])

    def test_multiple_continents(self):
        # Spanish spans Europe and the Americas (and Africa via Equatorial Guinea)
        continents = get_language_continents('es')
        self.assertIn('Europe', continents)
        self.assertIn('North America', continents)
        self.assertIn('South America', continents)

    def test_region_variant_matches_base(self):
        # zh-cn → country CN → Asia; zh-tw → country TW → Asia
        self.assertEqual(get_language_continents('zh-cn'), ['Asia'])
        self.assertEqual(get_language_continents('zh-tw'), ['Asia'])

    def test_pt_br_variant(self):
        # pt-br has region subtag 'br' (Brazil) → South America only, NOT
        # Africa/Asia/Europe where Portuguese is also spoken
        self.assertEqual(get_language_continents('pt-br'), ['South America'])

    def test_unknown_language_returns_empty(self):
        self.assertEqual(get_language_continents('xx-unknown'), [])

    def test_returns_sorted_list(self):
        continents = get_language_continents('fr')
        self.assertEqual(continents, sorted(continents))


if __name__ == '__main__':
    unittest.main()
