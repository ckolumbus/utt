from ...components.output import Output
from .. import formatter
from ..common import print_dicts
from .model import ProjectsModel


class ProjectsView:
    def __init__(self, model: ProjectsModel):
        self._model = model

    def render(self, output: Output) -> None:
        print(file=output)
        print(formatter.title("Projects"), file=output)
        print(file=output)

        fmt = "({duration_ratio}) {project:<{projects_max_length}}: {name}"
        print_dicts(self._model.projects, output, fmt)
