import urllib.parse
from logging import info

from urllib3 import PoolManager, Retry


def get_number_of_visitors(language: str, http: PoolManager) -> int:
    params = urllib.parse.urlencode(
        {'filters': f'[["contains","event:page",["/{language}/"]]]', 'period': 'all'}
    )
    response = http.request(
        'GET',
        f'https://plausible.io/api/stats/docs.python.org/top-stats/?{params}',
        retries=Retry(status_forcelist=(500, 502), backoff_factor=1, backoff_jitter=1),
    )
    info(f'visitors {response.status=} ({language=})')
    return response.json()['top_stats'][0]['value']


if __name__ == '__main__':
    print(get_number_of_visitors('pl', PoolManager()))
