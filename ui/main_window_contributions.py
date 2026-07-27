"""Contribuições visuais instaláveis pela MainWindow neutra."""

from contracts import ContributionCategory, ContributionRegistration
from core.contribution_manager import ContributionManager
from platform_sdk import (
    ActionContribution as WindowActionSpec,
    ToolbarContribution as WindowToolbarSpec,
    ViewContribution as WindowViewSpec,
)
from ui.views import (
    ActivitiesView,
    FunctionalAssignmentsView,
    FunctionalExercisesView,
)

def create_compatibility_contribution_manager() -> ContributionManager:
    """Cria o catálogo visual histórico enquanto o bootstrap não o fornece."""

    manager = ContributionManager()
    application_id = "rsc"
    manager.register_many((
        ContributionRegistration(
            ContributionCategory.ACTION,
            application_id,
            30,
            WindowActionSpec(
                attribute_name="action_activities",
                text="Atividades",
                menu_id="classification",
                tooltip="Visualizar atividades profissionais",
                object_name="actionActivities",
                enabled=False,
                disable_on_project_close=True,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.ACTION,
            application_id,
            20,
            WindowActionSpec(
                attribute_name="action_functional_assignments",
                text="Interpretações funcionais",
                menu_id="classification",
                visible=False,
                enabled=False,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.ACTION,
            application_id,
            10,
            WindowActionSpec(
                attribute_name="action_functional_exercises",
                text="Exercícios funcionais",
                menu_id="classification",
                visible=False,
                enabled=False,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            30,
            WindowToolbarSpec("main", "action_activities"),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            20,
            WindowToolbarSpec(
                "main",
                "action_functional_assignments",
            ),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            10,
            WindowToolbarSpec(
                "main",
                "action_functional_exercises",
            ),
        ),
        ContributionRegistration(
            ContributionCategory.VIEW,
            application_id,
            30,
            WindowViewSpec(
                "activities",
                "activities_view",
                ActivitiesView,
                "show_activities",
                open_project_action="action_open_project",
            ),
        ),
        ContributionRegistration(
            ContributionCategory.VIEW,
            application_id,
            20,
            WindowViewSpec(
                "functional_assignments",
                "functional_assignments_view",
                FunctionalAssignmentsView,
                "show_functional_assignments",
            ),
        ),
        ContributionRegistration(
            ContributionCategory.VIEW,
            application_id,
            10,
            WindowViewSpec(
                "functional_exercises",
                "functional_exercises_view",
                FunctionalExercisesView,
                "show_functional_exercises",
            ),
        ),
    ))
    from ui.dashboard_compatibility_contributions import (
        create_compatibility_dashboard_manager,
    )

    manager.register_many(
        create_compatibility_dashboard_manager().all_contributions()
    )
    return manager
