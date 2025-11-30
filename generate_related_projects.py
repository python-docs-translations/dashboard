import tomllib
from pathlib import Path
from shutil import copyfile, copytree

from jinja2 import Environment, FileSystemLoader


if __name__ == '__main__':
    Path('build').mkdir(parents=True, exist_ok=True)

    with open('related_projects.toml', 'rb') as f:
        data = tomllib.load(f)
    projects = data['projects']

    env = Environment(loader=FileSystemLoader('templates'))
    related = env.get_template('related.html.jinja').render(projects=projects)

    Path('build/related.html').write_text(related)
    copyfile('src/style.css', 'build/style.css')
    copyfile('src/logo.png', 'build/logo.png')
    copytree('src/images', 'build/images', dirs_exist_ok=True)
