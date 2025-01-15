from typing import Literal

pulling_from_transifex = ('zh-cn', 'pt-br', 'ja', 'uk', 'pl')

custom_contributing_links = {
    'es': 'https://python-docs-es.readthedocs.io/page/CONTRIBUTING.html',
    'ko': 'https://www.flowdas.com/pages/python-docs-ko.html',
    'zh-tw': 'https://github.com/python/python-docs-zh-tw/blob/3.13/README.rst#%E5%8F%83%E8%88%87%E7%BF%BB%E8%AD%AF',
    'fr': 'https://git.afpy.org/AFPy/python-docs-fr/src/branch/3.13/CONTRIBUTING.rst',
    'id': 'https://github.com/python/python-docs-id/blob/master/README.md#berkontribusi-untuk-menerjemahkan',
    'tr': 'https://github.com/python/python-docs-tr/blob/3.12/README.md#%C3%A7eviriye-katk%C4%B1da-bulunmak',
    'gr': 'https://github.com/pygreece/python-docs-gr/blob/3.12/CONTRIBUTING.md',
}


def get_contrib_link(language: str) -> str | Literal[False]:
    return custom_contributing_links.get(language) or (
        language in pulling_from_transifex
        and 'https://explore.transifex.com/python-doc/python-newest/'
    )


if __name__ == '__main__':
    for code in ('en', 'pl', 'ar', 'zh-cn', 'id'):
        print(f'{code}: {get_contrib_link(code)}')
