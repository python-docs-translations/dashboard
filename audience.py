from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path


def get_audience(
    stats_dir: Path,
    language_codes: Iterable[str],
    snapshots: int = 30,
    *,
    required: bool = False,
) -> dict[str, int]:
    """Return a rolling audience score for each language.

    Plausible's public exports contain one visitor count per hour, so the score
    is the sum of those counts across the most recent available snapshots.
    """
    if snapshots < 1:
        raise ValueError('snapshots must be at least 1')

    audience = dict.fromkeys(language_codes, 0)
    if not stats_dir.is_dir():
        message = f'Plausible statistics directory not found: {stats_dir}'
        if required:
            raise FileNotFoundError(message)
        logging.warning(message)
        return audience

    snapshot_dirs = sorted(
        (path for path in stats_dir.glob('docs.python.org_*') if path.is_dir()),
        key=lambda path: path.name,
        reverse=True,
    )
    if not snapshot_dirs:
        message = f'No Plausible statistics snapshots found in {stats_dir}'
        if required:
            raise FileNotFoundError(message)
        logging.warning(message)
        return audience

    snapshots_read = dict.fromkeys(audience, 0)
    files_read = 0
    for snapshot_dir in snapshot_dirs:
        for language_code in audience:
            if snapshots_read[language_code] >= snapshots:
                continue
            visitors_file = snapshot_dir / (
                f'{snapshot_dir.name}.prefix-{language_code}.visitors.json'
            )
            if not visitors_file.exists():
                continue

            rows = json.loads(visitors_file.read_text())
            audience[language_code] += sum(int(row['visitors']) for row in rows)
            snapshots_read[language_code] += 1
            files_read += 1

    if required and not files_read:
        raise FileNotFoundError(f'No Plausible visitor statistics found in {stats_dir}')

    return audience
