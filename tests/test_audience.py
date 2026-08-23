import json
import tempfile
import unittest
from pathlib import Path

import support

with support.import_scripts():
    from audience import get_audience


class TestAudience(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.stats_dir = Path(self.temporary_directory.name)

    def write_visitors(self, date, language_code, visitors):
        snapshot_name = f'docs.python.org_{date}'
        snapshot_dir = self.stats_dir / snapshot_name
        snapshot_dir.mkdir(exist_ok=True)
        (
            snapshot_dir / f'{snapshot_name}.prefix-{language_code}.visitors.json'
        ).write_text(json.dumps([{'visitors': value} for value in visitors]))

    def test_sums_hourly_visitors_from_most_recent_snapshots(self):
        self.write_visitors('2026-08-20', 'pl', ['2', '3'])
        self.write_visitors('2026-08-21', 'pl', ['5', '7'])
        self.write_visitors('2026-08-22', 'pl', ['11', '13'])

        audience = get_audience(self.stats_dir, ['pl'], snapshots=2)

        self.assertEqual(audience, {'pl': 36})

    def test_supports_hyphenated_codes_and_missing_languages(self):
        self.write_visitors('2026-08-22', 'pt-br', ['17'])

        audience = get_audience(self.stats_dir, ['pt-br', 'de'])

        self.assertEqual(audience, {'pt-br': 17, 'de': 0})

    def test_uses_older_snapshot_when_newer_one_is_missing(self):
        self.write_visitors('2026-08-20', 'pl', ['2'])
        self.write_visitors('2026-08-21', 'es', ['100'])
        self.write_visitors('2026-08-22', 'pl', ['5'])

        audience = get_audience(self.stats_dir, ['pl'], snapshots=2)

        self.assertEqual(audience, {'pl': 7})

    def test_missing_stats_directory_returns_zero(self):
        audience = get_audience(self.stats_dir / 'missing', ['pl'])

        self.assertEqual(audience, {'pl': 0})

    def test_malformed_schema_is_not_ignored(self):
        self.write_visitors('2026-08-22', 'pl', [None])

        with self.assertRaises(TypeError):
            get_audience(self.stats_dir, ['pl'])

    def test_requires_at_least_one_snapshot(self):
        with self.assertRaises(ValueError):
            get_audience(self.stats_dir, ['pl'], snapshots=0)

    def test_required_stats_must_contain_visitor_files(self):
        (self.stats_dir / 'docs.python.org_2026-08-22').mkdir()

        with self.assertRaises(FileNotFoundError):
            get_audience(self.stats_dir, ['pl'], required=True)


if __name__ == '__main__':
    unittest.main()
