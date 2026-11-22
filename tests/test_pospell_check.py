import copy
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import support
from urllib3.exceptions import HTTPError

with support.import_scripts():
    import pospell_check


class TestPospellCheck(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / 'warnings-pospell-pl.txt'
        self.repo = 'python/python-docs-pl'
        self.report = {
            'schema_version': 1,
            'status': 'complete',
            'repository': self.repo,
            'language': 'pl',
            'docs_version': '3.15',
            'created_at': '2026-11-21T00:00:00+00:00',
            'translations_revision': 'checked-commit',
            'run_url': f'https://github.com/{self.repo}/actions/runs/123',
            'catalogs': {
                'tutorial/guide.po': {
                    'findings': [
                        {
                            'msgctxt': 'context',
                            'msgid': 'Source',
                            'msgid_plural': 'Sources',
                            'words': ['Błont', 'literufka'],
                        }
                    ]
                },
                'bugs.po': {'findings': []},
            },
        }
        self.artifact = {
            'id': 1,
            'expired': False,
            'workflow_run': {
                'id': 123,
                'head_branch': '3.15',
                'repository_id': 10,
                'head_repository_id': 10,
            },
        }
        self.run = {
            'status': 'completed',
            'event': 'push',
            'conclusion': 'failure',
            'head_repository': {'full_name': self.repo},
        }
        self.api = self.enterContext(patch('pospell_check.github_api'))
        self.api.side_effect = self.github_api
        self.enterContext(patch('pospell_check.Path', return_value=self.output))

    def github_api(self, endpoint):
        if '/artifacts?' in endpoint:
            return json.dumps({'artifacts': [self.artifact]}).encode()
        if '/runs/' in endpoint:
            return json.dumps(self.run).encode()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('spellcheck.json', json.dumps(self.report))
        return archive.getvalue()

    def store(self):
        return pospell_check.store_and_count_failures(self.repo, '3.15', 'pl')

    def test_failed_run_with_complete_report_counts_entries_and_writes_log(self):
        self.assertEqual(self.store(), 1)
        log = self.output.read_text(encoding='utf-8')
        for text in (
            'tutorial/guide.po: Błont, literufka',
            'msgctxt: "context"',
            'msgid: "Source"',
            'msgid_plural: "Sources"',
            self.report['created_at'],
            self.report['translations_revision'],
            self.report['run_url'],
        ):
            self.assertIn(text, log)
        self.assertIn('name=spellcheck-pl', self.api.call_args_list[0].args[0])

    def test_clean_report_writes_zero(self):
        self.report['catalogs']['tutorial/guide.po']['findings'] = []
        self.assertEqual(self.store(), 0)
        self.assertIn('Entries with spelling findings: 0', self.output.read_text())

    def test_missing_report_removes_previous_log(self):
        self.output.write_text('old findings')
        self.api.side_effect = None
        self.api.return_value = b'{"artifacts": []}'
        self.assertIsNone(self.store())
        self.assertFalse(self.output.exists())

    def test_expired_wrong_branch_and_fork_artifacts_are_skipped(self):
        candidates = [copy.deepcopy(self.artifact) for _ in range(3)]
        candidates[0]['expired'] = True
        candidates[1]['workflow_run']['head_branch'] = '3.14'
        candidates[2]['workflow_run']['head_repository_id'] = 99
        self.api.side_effect = None
        self.api.return_value = json.dumps({'artifacts': candidates}).encode()
        self.assertIsNone(self.store())
        self.assertEqual(self.api.call_count, 1)
        self.assertFalse(self.output.exists())

    def test_pr_incomplete_and_wrong_repository_runs_are_skipped(self):
        for changes in (
            {'event': 'pull_request'},
            {'event': 'pull_request_target'},
            {'status': 'in_progress'},
            {'head_repository': {'full_name': 'fork/python-docs-pl'}},
        ):
            with self.subTest(changes=changes):
                original = self.run.copy()
                self.run.update(changes)
                self.assertIsNone(self.store())
                self.assertFalse(self.output.exists())
                self.run = original

    def test_incompatible_or_malformed_reports_are_unavailable(self):
        for field, value in (
            ('schema_version', 2),
            ('status', 'error'),
            ('repository', 'fork/python-docs-pl'),
            ('language', 'fr'),
            ('docs_version', '3.14'),
            ('catalogs', []),
            ('catalogs', {'bugs.po': {'findings': None}}),
            ('catalogs', {'bugs.po': {'findings': [{}]}}),
        ):
            with self.subTest(field=field, value=value):
                original = self.report.copy()
                self.report[field] = value
                self.assertIsNone(self.store())
                self.assertFalse(self.output.exists())
                self.report = original

    def test_older_complete_report_is_used_after_incomplete_report(self):
        original_api = self.github_api

        def api(endpoint):
            if '/artifacts?' in endpoint:
                return json.dumps(
                    {'artifacts': [self.artifact, {**self.artifact, 'id': 2}]}
                ).encode()
            self.report['status'] = 'error' if '/1/zip' in endpoint else 'complete'
            return original_api(endpoint)

        self.api.side_effect = api
        self.assertEqual(self.store(), 1)

    def test_artifacts_are_paginated(self):
        expired = {**self.artifact, 'expired': True}
        original_api = self.github_api

        def api(endpoint):
            if '/artifacts?' in endpoint and '&page=1' in endpoint:
                return json.dumps({'artifacts': [expired] * 100}).encode()
            return original_api(endpoint)

        self.api.side_effect = api
        self.assertEqual(self.store(), 1)
        self.assertIn('page=2', self.api.call_args_list[1].args[0])

    def test_download_failure_is_unavailable_and_removes_old_log(self):
        self.output.write_text('old findings')
        self.api.side_effect = HTTPError('Forbidden')
        with self.assertLogs('pydocs-translation-dashboard', level='WARNING'):
            self.assertIsNone(self.store())
        self.assertFalse(self.output.exists())

    def test_corrupt_archive_is_skipped(self):
        original_api = self.github_api
        self.api.side_effect = lambda endpoint: (
            b'not a zip' if endpoint.endswith('/zip') else original_api(endpoint)
        )
        self.assertIsNone(self.store())
        self.assertFalse(self.output.exists())


class TestGitHubAPI(unittest.TestCase):
    def test_authentication_and_http_errors(self):
        with (
            patch.dict(os.environ, {'GH_TOKEN': 'test-token'}),
            patch('pospell_check.request') as request,
        ):
            request.return_value.status = 200
            request.return_value.data = b'report'
            self.assertEqual(pospell_check.github_api('repos/owner/repo'), b'report')
            self.assertEqual(
                request.call_args.kwargs['headers']['Authorization'],
                'Bearer test-token',
            )
            request.return_value.status = 403
            with self.assertRaises(HTTPError):
                pospell_check.github_api('repos/owner/repo')
