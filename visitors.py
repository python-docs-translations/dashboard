import csv
import io
import logging
import urllib.parse
import zipfile

from requests import Session


def get_number_of_visitors(language: str, requests: Session) -> int:
    params = urllib.parse.urlencode(
        {'filters': f'[["contains","event:page",["/{language}/"]]]', 'period': 'all'}
    )
    for _ in range(2):
        r = requests.get(
            f'https://plausible.io/docs.python.org/export?{params}', timeout=40
        )
        try:
            with (
                zipfile.ZipFile(io.BytesIO(r.content), 'r') as z,
                z.open('visitors.csv') as csv_file,
            ):
                csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
                return sum(int(row['visitors']) for row in csv_reader)
        except zipfile.BadZipFile as bad_zip_file:
            logging.exception(
                f'Plausible responded with broken archive for {language}. Retrying.'
            )
            exception = bad_zip_file
            continue
    raise exception
