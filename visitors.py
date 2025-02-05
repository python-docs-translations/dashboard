import csv
import io
import logging
import urllib.parse
import zipfile

from urllib3 import PoolManager


def get_number_of_visitors(language: str, http: PoolManager) -> int:
    params = urllib.parse.urlencode(
        {'filters': f'[["contains","event:page",["/{language}/"]]]', 'period': 'all'}
    )
    r = http.request('GET', f'https://plausible.io/docs.python.org/export?{params}')
    logging.info(f'Plausible export responded with {r.status=}')
    with (
        zipfile.ZipFile(io.BytesIO(r.data), 'r') as z,
        z.open('visitors.csv') as csv_file,
    ):
        csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
        return sum(int(row['visitors']) for row in csv_reader)


if __name__ == '__main__':
    print(get_number_of_visitors('pl', PoolManager()))
