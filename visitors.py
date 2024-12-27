import csv
import io
import urllib
import zipfile

import requests


def get_number_of_visitors(language: str) -> tuple[int, float | None]:
    param = urllib.parse.urlencode({'filters': f'[["contains","event:page",["/{language}/"]]]'})
    r = requests.get(f'https://plausible.io/docs.python.org/export?{param}', timeout=10)
    d = languages_data.get(language)
    p = d and (d['native_speakers_millions'] * d['literacy_rate_percentage'] + d["second_language_learners_millions"] * 10e6)
    with zipfile.ZipFile(io.BytesIO(r.content), 'r') as z, z.open('visitors.csv') as csv_file:
        csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
        sum_ = sum(int(row["visitors"]) for row in csv_reader)
        return sum_, p and (sum_ / p * 10000)

languages_data = {
    "ar": {"native_speakers_millions": 310, "literacy_rate_percentage": 76, "second_language_learners_millions": 24},
    "bn-in": {"native_speakers_millions": 230, "literacy_rate_percentage": 74, "second_language_learners_millions": 20},
    "es": {"native_speakers_millions": 495, "literacy_rate_percentage": 97, "second_language_learners_millions": 24},
    "fa": {"native_speakers_millions": 80, "literacy_rate_percentage": 85, "second_language_learners_millions": 50},
    "fr": {"native_speakers_millions": 80, "literacy_rate_percentage": 99, "second_language_learners_millions": 200},
    "gr": {"native_speakers_millions": 13, "literacy_rate_percentage": 97, "second_language_learners_millions": 0.4},
    "id": {"native_speakers_millions": 43, "literacy_rate_percentage": 96, "second_language_learners_millions": 12},
    "it": {"native_speakers_millions": 67, "literacy_rate_percentage": 99, "second_language_learners_millions": 2},
    "hi-in": {"native_speakers_millions": 341, "literacy_rate_percentage": 74, "second_language_learners_millions": 120},
    "hu": {"native_speakers_millions": 13, "literacy_rate_percentage": 99.1, "second_language_learners_millions": 2},
    "ja": {"native_speakers_millions": 125, "literacy_rate_percentage": 99, "second_language_learners_millions": 3},
    "ko": {"native_speakers_millions": 81, "literacy_rate_percentage": 98, "second_language_learners_millions": 13},
    "lt": {"native_speakers_millions": 3, "literacy_rate_percentage": 99.8, "second_language_learners_millions": 0.2},
    "mr": {"native_speakers_millions": 83, "literacy_rate_percentage": 82.9, "second_language_learners_millions": 3},
    "pl": {"native_speakers_millions": 38, "literacy_rate_percentage": 98, "second_language_learners_millions": 2},
    "pt": {"native_speakers_millions": 232, "literacy_rate_percentage": 93.5, "second_language_learners_millions": 25},
    "pt-br": {"native_speakers_millions": 260, "literacy_rate_percentage": 94, "second_language_learners_millions": 10},
    "ru": {"native_speakers_millions": 154, "literacy_rate_percentage": 99.7, "second_language_learners_millions": 61},
    "tr": {"native_speakers_millions": 88, "literacy_rate_percentage": 96, "second_language_learners_millions": 5},
    "uk": {"native_speakers_millions": 40, "literacy_rate_percentage": 99, "second_language_learners_millions": 2},
    "zh-cn": {"native_speakers_millions": 920, "literacy_rate_percentage": 96, "second_language_learners_millions": 300},
    "zh-tw": {"native_speakers_millions": 25, "literacy_rate_percentage": 98, "second_language_learners_millions": 20},
}