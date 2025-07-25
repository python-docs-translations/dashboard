import json
import concurrent.futures
import itertools
import logging
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from git import Repo
from jinja2 import Environment, FileSystemLoader, Template
from urllib3 import PoolManager

import build_status
import contribute
from completion import branches_from_devguide, get_completion, TranslatorsData
from counts import get_counts
from repositories import Language, get_languages_and_repos

generation_time = datetime.now(timezone.utc)


def get_completion_progress() -> Iterator['LanguageProjectData']:
    clones_dir = Path('clones')
    Repo.clone_from(
        'https://github.com/python/devguide.git',
        devguide_dir := Path(clones_dir, 'devguide'),
        depth=1,
    )
    latest_branch = branches_from_devguide(devguide_dir)[0]
    Repo.clone_from(
        'https://github.com/python/cpython.git',
        cpython_dir := Path(clones_dir, 'cpython'),
        depth=1,
        branch=latest_branch,
    )
    subprocess.run(['make', '-C', cpython_dir / 'Doc', 'venv'], check=True)
    subprocess.run(['make', '-C', cpython_dir / 'Doc', 'gettext'], check=True)
    languages_built = dict(build_status.get_languages(PoolManager()))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.map(
            get_project_data,
            *zip(*get_languages_and_repos(devguide_dir)),
            itertools.repeat(languages_built),
            itertools.repeat(clones_dir),
        )


def get_project_data(
    language: Language,
    repo: str | None,
    languages_built: dict[str, bool],
    clones_dir: str,
) -> 'LanguageProjectData':
    built = language.code in languages_built
    if repo:
        completion, translators_data, branch, change = get_completion(clones_dir, repo)
    else:
        completion = 0.0
        translators_data = TranslatorsData(0, False)
        change = 0.0
        branch = ''
    return LanguageProjectData(
        language,
        repo,
        branch,
        completion,
        change,
        translators_data,
        built,
        in_switcher=languages_built.get(language.code),
        uses_platform=language.code in contribute.pulling_from_transifex,
        contribution_link=contribute.get_contrib_link(language.code, repo),
    )


@dataclass(frozen=True)
class LanguageProjectData:
    language: Language
    repository: str | None
    branch: str
    completion: float
    change: float
    translators: TranslatorsData
    built: bool
    in_switcher: bool | None
    uses_platform: bool
    contribution_link: str | None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info(f'starting at {generation_time}')
    Path('build').mkdir(parents=True, exist_ok=True)

    #completion_progress = list(get_completion_progress())
    completion_progress = [LanguageProjectData(language=Language(code='ar', name='Arabic'), repository='Abdur-rahmaanJ/python-docs-ar', branch='master', completion=0.013630393298803004, change=0.0, translators=TranslatorsData(number=3, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/Abdur-rahmaanJ/python-docs-ar'), LanguageProjectData(language=Language(code='bn-in', name='Bengali'), repository='python/python-docs-bn-in', branch='3.14', completion=0.10904314639042403, change=0.0, translators=TranslatorsData(number=1, link=False), built=True, in_switcher=False, uses_platform=False, contribution_link='https://github.com/python/python-docs-bn-in'), LanguageProjectData(language=Language(code='fr', name='French'), repository='python/python-docs-fr', branch='3.13', completion=32.880226016703425, change=0.0, translators=TranslatorsData(number=241, link='https://github.com/python/python-docs-fr/blob/3.13/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://git.afpy.org/AFPy/python-docs-fr/src/branch/3.13/CONTRIBUTING.rst'), LanguageProjectData(language=Language(code='el', name='Greek'), repository='python/python-docs-el', branch='3.14', completion=7.6354985006567375, change=0.29367301925602884, translators=TranslatorsData(number=15, link='https://github.com/python/python-docs-el/blob/3.14/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://github.com/python/python-docs-el'), LanguageProjectData(language=Language(code='hi-in', name='Hindi'), repository='CuriousLearner/python-docs-hi-in', branch='master', completion=0.004956506654110183, change=0.0, translators=TranslatorsData(number=1, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/CuriousLearner/python-docs-hi-in'), LanguageProjectData(language=Language(code='hu', name='Hungarian'), repository='python/python-docs-hu', branch='master', completion=0.0, change=0.0, translators=TranslatorsData(number=1, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/python/python-docs-hu'), LanguageProjectData(language=Language(code='id', name='Indonesian'), repository='python/python-docs-id', branch='3.14', completion=0.0, change=0.0, translators=TranslatorsData(number=25, link='https://github.com/python/python-docs-id/blob/3.14/TRANSLATORS'), built=True, in_switcher=False, uses_platform=False, contribution_link='https://github.com/python/python-docs-id/blob/master/README.md#berkontribusi-untuk-menerjemahkan'), LanguageProjectData(language=Language(code='it', name='Italian'), repository='python/python-docs-it', branch='3.13', completion=3.351837624842011, change=0.0, translators=TranslatorsData(number=3, link='https://github.com/python/python-docs-it/blob/3.13/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://github.com/python/python-docs-it'), LanguageProjectData(language=Language(code='ja', name='Japanese'), repository='python/python-docs-ja', branch='3.14', completion=49.79430497385443, change=0.04336943322346798, translators=TranslatorsData(number=13, link=False), built=True, in_switcher=True, uses_platform=True, contribution_link='https://explore.transifex.com/python-doc/python-newest/'), LanguageProjectData(language=Language(code='ko', name='Korean'), repository='python/python-docs-ko', branch='3.13', completion=45.986468736834276, change=0.2478253327055029, translators=TranslatorsData(number=23, link='https://github.com/python/python-docs-ko/blob/3.13/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://www.flowdas.com/pages/python-docs-ko.html'), LanguageProjectData(language=Language(code='mr', name='Marathi'), repository='sanketgarade/python-doc-mr', branch='3.9', completion=0.0, change=0.0, translators=TranslatorsData(number=1, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/sanketgarade/python-doc-mr'), LanguageProjectData(language=Language(code='lt', name='Lithuanian'), repository=None, branch='', completion=0.0, change=0.0, translators=TranslatorsData(number=0, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link=None), LanguageProjectData(language=Language(code='fa', name='Persian'), repository='revisto/python-docs-fa', branch='3.13', completion=0.0, change=0.0, translators=TranslatorsData(number=9, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/revisto/python-docs-fa'), LanguageProjectData(language=Language(code='pl', name='Polish'), repository='python/python-docs-pl', branch='3.14', completion=40.93083194964189, change=29.423062625461576, translators=TranslatorsData(number=9, link=False), built=True, in_switcher=True, uses_platform=True, contribution_link='https://explore.transifex.com/python-doc/python-newest/'), LanguageProjectData(language=Language(code='pt', name='Portuguese'), repository=None, branch='', completion=0.0, change=0.0, translators=TranslatorsData(number=0, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link=None), LanguageProjectData(language=Language(code='pt-br', name='Brazilian Portuguese'), repository='python/python-docs-pt-br', branch='3.14', completion=62.121137022626456, change=1.494386756214226, translators=TranslatorsData(number=3, link=False), built=True, in_switcher=True, uses_platform=True, contribution_link='https://explore.transifex.com/python-doc/python-newest/'), LanguageProjectData(language=Language(code='ro', name='Romanian'), repository='python/python-docs-ro', branch='main', completion=1.192039850313499, change=0.49317241208396323, translators=TranslatorsData(number=1, link='https://github.com/python/python-docs-ro/blob/main/TRANSLATORS'), built=True, in_switcher=False, uses_platform=False, contribution_link='https://github.com/python/python-docs-ro'), LanguageProjectData(language=Language(code='ru', name='Russian'), repository='MLGRussianXP/python-docs-ru', branch='3.14', completion=0.19578201283735222, change=0.008673886644692819, translators=TranslatorsData(number=3, link=False), built=False, in_switcher=None, uses_platform=False, contribution_link='https://github.com/MLGRussianXP/python-docs-ru'), LanguageProjectData(language=Language(code='zh-cn', name='Simplified Chinese'), repository='python/python-docs-zh-cn', branch='3.14', completion=96.77950980149191, change=20.155634308939057, translators=TranslatorsData(number=224, link=False), built=True, in_switcher=True, uses_platform=True, contribution_link='https://explore.transifex.com/python-doc/python-newest/'), LanguageProjectData(language=Language(code='es', name='Spanish'), repository='python/python-docs-es', branch='3.13', completion=57.77551981363535, change=0.026021659934073682, translators=TranslatorsData(number=314, link='https://github.com/python/python-docs-es/blob/3.13/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html'), LanguageProjectData(language=Language(code='zh-tw', name='Traditional Chinese'), repository='python/python-docs-zh-tw', branch='3.13', completion=37.15273475254641, change=1.7174295556491828, translators=TranslatorsData(number=124, link='https://github.com/python/python-docs-zh-tw/blob/3.13/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://github.com/python/python-docs-zh-tw/blob/3.13/README.rst#%E5%8F%83%E8%88%87%E7%BF%BB%E8%AD%AF'), LanguageProjectData(language=Language(code='tr', name='Turkish'), repository='python/python-docs-tr', branch='3.12', completion=4.693811801442344, change=0.0, translators=TranslatorsData(number=30, link='https://github.com/python/python-docs-tr/blob/3.12/TRANSLATORS'), built=True, in_switcher=True, uses_platform=False, contribution_link='https://github.com/python/python-docs-tr/blob/3.12/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak'), LanguageProjectData(language=Language(code='uk', name='Ukrainian'), repository='python/python-docs-uk', branch='3.13', completion=49.25280662189289, change=0.0, translators=TranslatorsData(number=13, link=False), built=True, in_switcher=False, uses_platform=True, contribution_link='https://explore.transifex.com/python-doc/python-newest/')]
    #counts = get_counts(Path('clones', 'cpython', 'Doc', 'build', 'gettext'))
    counts = 11, 22

    env = Environment(loader=FileSystemLoader("templates"))
    index = env.get_template('index.html.jinja').render(
        completion_progress=completion_progress,
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
        counts=counts,
    )

    chart = env.get_template('chart.html.jinja').render(
        completion_progress=completion_progress,
        generation_time=generation_time,
        duration=(datetime.now(timezone.utc) - generation_time).seconds,
        counts=counts,
    )

    lang_template = env.get_template('language.html.jinja')
    for language_data in completion_progress:
        language = language_data.language
        code = language.code

        html = lang_template.render(
            language=language_data,
        )

        Path(f'build/{code}.html').write_text(html)

    Path('build/style.css').write_bytes(Path('src/style.css').read_bytes())
    Path('build/logo.png').write_bytes(Path('src/logo.png').read_bytes())
    Path('build/index.html').write_text(index)
    Path('build/chart.html').write_text(chart)
    Path('build/index.json').write_text(
        json.dumps(completion_progress, indent=2, default=asdict)
    )
