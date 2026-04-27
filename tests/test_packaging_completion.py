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

    def test_zh_hans(self):
        self.assertEqual(packaging_completion._rtd_code_to_locale('zh-hans'), 'zh_HANS')


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
