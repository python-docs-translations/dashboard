from pathlib import Path
from shutil import copyfile

import sphinx.cmd.build


def number(clones_dir: str, repo: str, language_code: str) -> int:
    language_part, *locale = language_code.split('-')
    if locale:
        lang_with_locale = f'{language_part}_{locale[0].upper()}'
    else:
        lang_with_locale = language_part
    locale_dir = Path(clones_dir, f'cpython/Doc/locales/{lang_with_locale}/LC_MESSAGES')
    locale_dir.mkdir(parents=True)
    for po_file in Path(clones_dir, repo).rglob('*.po'):
        relative_path = po_file.relative_to(Path(clones_dir, repo))
        target_file = locale_dir / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        copyfile(po_file, target_file)
    sphinx.cmd.build.main(
        (
            '--builder',
            'html',
            '--jobs',
            'auto',
            '--define',
            f'language={language_code}',
            '--verbose',
            '--warning-file',
            warning_file := f'{clones_dir}/warnings-{language_code}.txt',
            f'{clones_dir}/cpython/Doc',  # sourcedir
            f'./sphinxbuild/{language_code}',  # outputdir
        )
    )
    copyfile(warning_file, f'warnings-{language_code}.txt')
    return len(Path(warning_file).read_text().splitlines())
