pulling_from_transifex: tuple[str, ...] = (
    'zh-cn',
    'pt-br',
    'ja',
    'uk',
    'pl',
    'ru',
    'fa',
    'id',
)

custom_contributing_links: dict[str, str] = {
    'es': 'https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html',
    'ko': 'https://www.flowdas.com/pages/python-docs-ko.html',
    'zh-tw': 'https://github.com/python/python-docs-zh-tw/blob/3.13/README.rst#%E5%8F%83%E8%88%87%E7%BF%BB%E8%AD%AF',
    'fr': 'https://git.afpy.org/AFPy/python-docs-fr/src/branch/3.13/CONTRIBUTING.rst',
    'id': 'https://github.com/python/python-docs-id/blob/3.14/README.md#berkontribusi-untuk-menerjemahkan',
    'tr': 'https://github.com/python/python-docs-tr/blob/3.12/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak',
    'el': 'https://github.com/python/python-docs-el/blob/3.14/CONTRIBUTING.md',
    'pt-br': 'https://python.org.br/traducao/',
}


def get_contrib_link(language: str, repo: str | None) -> str | None:
    return (
        custom_contributing_links.get(language)
        or (
            language in pulling_from_transifex
            and 'https://explore.transifex.com/python-doc/python-newest/'
        )
        or (repo and f'https://github.com/{repo}')
    )
