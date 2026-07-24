"""Implementação mínima da Application RSC."""

from contracts import ActionContribution
from models import Project


class RscApplication:
    """Identidade e compatibilidade arquitetural da Application RSC."""

    application_id = "rsc"
    display_name = "RSC"

    def can_open(self, project: Project) -> bool:
        return (
            isinstance(project, Project)
            and project.application == self.application_id
        )

    def contributions(self) -> tuple[ActionContribution, ...]:
        return ()
