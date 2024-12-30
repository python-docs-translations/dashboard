from datetime import datetime
from pathlib import Path

from jinja2 import Template

template = Template(Path("template.html").read_text())
output = template.render(completion_progress=(), generation_time=datetime.now())

with open("index.html", "w") as file:
    file.write(output)
