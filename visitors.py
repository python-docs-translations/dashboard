import csv
import io
import urllib.parse
import zipfile

import backoff
from requests import Session


@backoff.on_exception(backoff.expo, zipfile.BadZipFile, max_tries=5)
def get_number_of_visitors(language: str, requests: Session) -> int:
    params = urllib.parse.urlencode(
        {'filters': f'[["contains","event:page",["/{language}/"]]]', 'period': 'all'}
    )
    r = requests.get(
        f'https://plausible.io/docs.python.org/export?{params}', timeout=40
    )
    with (
        zipfile.ZipFile(io.BytesIO(r.content), 'r') as z,
        z.open('visitors.csv') as csv_file,
    ):
        csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
        return sum(int(row['visitors']) for row in csv_reader)
