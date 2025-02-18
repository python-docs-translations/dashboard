import csv
import io
import urllib.parse
import zipfile
from logging import info

from urllib3 import PoolManager, Retry


def get_number_of_visitors(language: str, http: PoolManager) -> int:
    params = urllib.parse.urlencode(
        {'filters': f'[["contains","event:page",["/{language}/"]]]', 'period': 'all'}
    )
    response = http.request(
        'GET',
        f'https://plausible.io/docs.python.org/export?{params}',
        retries=Retry(status_forcelist=(500,502)),
    )
    info(f'visitors {response.status=} ({language=})')
    with (
        zipfile.ZipFile(io.BytesIO(response.data), 'r') as z,
        z.open('visitors.csv') as csv_file,
    ):
        csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
        return sum(int(row['visitors']) for row in csv_reader)


if __name__ == '__main__':
    print(get_number_of_visitors('pl', PoolManager()))
