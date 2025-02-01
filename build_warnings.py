from pathlib import Path
from shutil import copyfile

import sphinx.cmd.build


def number(clones_dir: str, repo: str, language_code: str) -> int:
    Path(clones_dir, f'cpython/Doc/locales/{language_code}').mkdir(parents=True)
    Path(clones_dir, f'cpython/Doc/locales/{language_code}/LC_MESSAGES').symlink_to(
        Path(clones_dir, repo), True
    )
    sphinx.cmd.build.main(
        (
            '--builder',
            'html',
            '--fresh-env',
            '--jobs',
            'auto',
            '--define',
            f'language={language_code}',
            '--verbose',
            '--warning-file',
            warning_file := f'{clones_dir}/warnings-{language_code}.txt',
            f'{clones_dir}/cpython/Doc',  # sourcedir
            './build',  # outputdir
        )
    )
    copyfile(warning_file, f'warnings-{language_code}.txt')
    return len(Path(warning_file).read_text().splitlines())
