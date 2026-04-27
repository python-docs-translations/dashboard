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


if __name__ == '__main__':
    unittest.main()
