import csv
import io
import urllib
import zipfile

import humanize
import requests


def get_number_of_visitors(language: str) -> str:
    param = urllib.parse.urlencode({'filters': f'[["contains","event:page",["/{language}/"]]]'})
    r = requests.get(f'https://plausible.io/docs.python.org/export?{param}', timeout=10)
    with zipfile.ZipFile(io.BytesIO(r.content), 'r') as z, z.open('visitors.csv') as csv_file:
        csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
        return f"{sum(int(row["visitors"]) for row in csv_reader):,}"
