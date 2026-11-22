"""Fetch spelling results published by translation repositories."""

import io
import json
import logging
import os
import zipfile
from pathlib import Path
from urllib.parse import urlencode

from urllib3 import request
from urllib3.exceptions import HTTPError

logger = logging.getLogger('pydocs-translation-dashboard')


def github_api(endpoint: str) -> bytes:
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    if token := os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = f'Bearer {token}'
    response = request(
        'GET', f'https://api.github.com/{endpoint}', headers=headers, timeout=30
    )
    if response.status != 200:
        raise HTTPError(f'GitHub returned HTTP {response.status} for {endpoint}')
    return response.data


def download_report(repo: str, branch: str, language_code: str) -> dict | None:
    """Find the newest complete report, including runs with spelling failures."""
    page = 1
    while True:
        query = urlencode(
            {'name': f'spellcheck-{language_code}', 'per_page': 100, 'page': page}
        )
        artifacts = json.loads(github_api(f'repos/{repo}/actions/artifacts?{query}'))[
            'artifacts'
        ]
        for artifact in artifacts:
            run = artifact['workflow_run']
            if (
                artifact['expired']
                or run['head_branch'] != branch
                or run['head_repository_id'] != run['repository_id']
            ):
                continue
            details = json.loads(github_api(f'repos/{repo}/actions/runs/{run["id"]}'))
            if (
                details['status'] != 'completed'
                or details['event'] not in {'push', 'schedule', 'workflow_dispatch'}
                or details['head_repository']['full_name'] != repo
            ):
                continue
            try:
                archive = github_api(
                    f'repos/{repo}/actions/artifacts/{artifact["id"]}/zip'
                )
                with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                    report = json.loads(zipped.read('spellcheck.json'))
                if (
                    isinstance(report, dict)
                    and report.get('schema_version') == 1
                    and report.get('status') == 'complete'
                    and report.get('repository') == repo
                    and report.get('language') == language_code
                    and report.get('docs_version') == branch
                ):
                    # Validate findings before accepting a candidate as usable.
                    format_failures(report)
                    return report
            except (ValueError, KeyError, TypeError, zipfile.BadZipFile):
                logger.warning(
                    'Invalid pospell artifact %s in %s', artifact['id'], repo
                )
        if len(artifacts) < 100:
            return None
        page += 1


def format_failures(report: dict) -> list[str]:
    """Count affected entries, retaining their identities and suspect words."""
    failures = []
    if not isinstance(report['catalogs'], dict):
        raise TypeError('Invalid pospell catalogs')
    for resource, catalog in sorted(report['catalogs'].items()):
        if not isinstance(catalog, dict) or not isinstance(
            catalog.get('findings'), list
        ):
            raise TypeError('Invalid pospell findings')
        for finding in catalog['findings']:
            if (
                not isinstance(finding, dict)
                or not isinstance(finding.get('msgid'), str)
                or not isinstance(finding.get('words'), list)
                or not finding['words']
                or not all(isinstance(word, str) for word in finding['words'])
            ):
                raise ValueError('Invalid pospell finding')
            message = f'{resource}: {", ".join(finding["words"])}\n'
            for field in ('msgctxt', 'msgid', 'msgid_plural'):
                if finding.get(field) is not None:
                    message += (
                        f'  {field}: {json.dumps(finding[field], ensure_ascii=False)}\n'
                    )
            failures.append(message)
    return failures


def store_and_count_failures(repo: str, branch: str, language_code: str) -> int | None:
    filepath = Path(f'build/warnings-pospell-{language_code}.txt')
    report_path = filepath.with_name(f'spellcheck-{language_code}.json')
    # Deploys retain existing files, so explicitly replace unavailable reports.
    report_path.write_text('null\n', encoding='utf-8')
    filepath.unlink(missing_ok=True)
    try:
        report = download_report(repo, branch, language_code)
    except (HTTPError, ValueError, KeyError, TypeError) as error:
        logger.warning('Cannot fetch pospell report for %s: %s', repo, error)
        return None
    if report is None:
        return None
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    failures = format_failures(report)
    header = '\n'.join(
        f'{field}: {report.get(field, "")}'
        for field in (
            'repository',
            'docs_version',
            'created_at',
            'translations_revision',
            'run_url',
        )
    )
    filepath.write_text(
        f'{header}\nEntries with spelling findings: {len(failures)}\n\n'
        + '\n'.join(failures),
        encoding='utf-8',
    )
    return len(failures)
