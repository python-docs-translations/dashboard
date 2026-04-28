import unittest
import tempfile
import support

with support.import_scripts():
    import packaging_completion


class TestRtdCodeToLocale(unittest.TestCase):
    def test_simple_code(self):
        self.assertEqual(packaging_completion._rtd_code_to_locale('ja'), 'ja')

    def test_hyphenated_code(self):
        self.assertEqual(packaging_completion._rtd_code_to_locale('pt-br'), 'pt_BR')

    def test_zh_cn_maps_to_zh_hans(self):
        self.assertEqual(packaging_completion._rtd_code_to_locale('zh-cn'), 'zh_Hans')

    def test_zh_tw_maps_to_zh_hant(self):
        self.assertEqual(packaging_completion._rtd_code_to_locale('zh-tw'), 'zh_Hant')


class TestLocaleToRtdCodeOverrides(unittest.TestCase):
    def test_zh_hans_maps_to_zh_cn(self):
        self.assertEqual(
            packaging_completion.LOCALE_TO_RTD_CODE_OVERRIDES['zh_Hans'], 'zh-cn'
        )

    def test_zh_hant_maps_to_zh_tw(self):
        self.assertEqual(
            packaging_completion.LOCALE_TO_RTD_CODE_OVERRIDES['zh_Hant'], 'zh-tw'
        )


class TestLocaleCodeNormalisation(unittest.TestCase):
    def test_hi_in_normalises_to_hi(self):
        self.assertEqual(packaging_completion.LOCALE_CODE_NORMALISATION['hi_IN'], 'hi')

    def test_hi_in_rtd_normalises_to_hi(self):
        self.assertEqual(packaging_completion.LOCALE_CODE_NORMALISATION['hi-in'], 'hi')


class TestPoCompletion(unittest.TestCase):
    def test_missing_file_returns_zero(self):
        from pathlib import Path

        result = packaging_completion._po_completion(Path('/nonexistent/messages.po'))
        self.assertEqual(result, 0.0)

    def test_malformed_file_returns_zero(self):
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix='.po', mode='w', delete=False) as f:
            f.write('this is not a valid po file\x00\xff\xfe')
            tmp_path = Path(f.name)
        try:
            result = packaging_completion._po_completion(tmp_path)
            self.assertEqual(result, 0.0)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_returns_percentage_scale(self):
        """Completion is reported on a 0–100 scale, not 0–1."""
        from pathlib import Path

        po_content = (
            'msgid ""\n'
            'msgstr ""\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '\n'
            'msgid "hello"\n'
            'msgstr "hola"\n'
        )
        with tempfile.NamedTemporaryFile(suffix='.po', mode='w', delete=False) as f:
            f.write(po_content)
            tmp_path = Path(f.name)
        try:
            result = packaging_completion._po_completion(tmp_path)
            self.assertAlmostEqual(result, 100.0)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_fuzzy_entries_included(self):
        """percent_translated counts fuzzy as untranslated (not excluded from total)."""
        from pathlib import Path

        po_content = (
            'msgid ""\n'
            'msgstr ""\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '\n'
            'msgid "hello"\n'
            'msgstr "hola"\n'
            '\n'
            '#, fuzzy\n'
            'msgid "world"\n'
            'msgstr "mundo"\n'
            '\n'
            'msgid "foo"\n'
            'msgstr ""\n'
        )
        with tempfile.NamedTemporaryFile(suffix='.po', mode='w', delete=False) as f:
            f.write(po_content)
            tmp_path = Path(f.name)
        try:
            result = packaging_completion._po_completion(tmp_path)
            # polib percent_translated: 1 translated out of 3 total → 33 (int, rounded)
            self.assertEqual(result, 33)
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
