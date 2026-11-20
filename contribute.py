pulling_from_transifex: frozenset[str] = frozenset(
    {'zh-cn', 'pt-br', 'ja', 'uk', 'pl', 'ru', 'id'}
)

# Custom links take precedence. Otherwise, languages in pulling_from_transifex
# link to Transifex even if they have a repository; remaining languages link to
# their repository or, if unavailable, the general translation guide.
custom_contributing_links: dict[str, str] = {
    'es': 'https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html',
    'ko': 'https://www.flowdas.com/pages/python-docs-ko.html',
    'zh-tw': 'https://github.com/python/python-docs-zh-tw/blob/{branch}/README.rst#id2',
    'fr': 'https://git.afpy.org/AFPy/python-docs-fr/src/branch/{branch}/CONTRIBUTING.rst',
    'id': 'https://github.com/python/python-docs-id/blob/{branch}/README.md#berkontribusi-untuk-menerjemahkan',
    'tr': 'https://github.com/python/python-docs-tr/blob/{branch}/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak',
    'el': 'https://github.com/python/python-docs-el/blob/{branch}/CONTRIBUTING.md',
    'pt-br': 'https://python.org.br/traducao/',
}


def get_contrib_link(language: str, repo: str | None, branch: str) -> str | None:
    if link := custom_contributing_links.get(language):
        return link.format(branch=branch)

    return (
        (
            language in pulling_from_transifex
            and 'https://explore.transifex.com/python-doc/python-newest/'
        )
        or (repo and f'https://github.com/{repo}')
        or 'https://devguide.python.org/documentation/translations/translating/'
    )
