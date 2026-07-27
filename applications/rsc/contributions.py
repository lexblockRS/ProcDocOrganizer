"""Contribuições estáticas do RSC declaradas pelo Platform SDK."""

from contracts import ContributionCategory, ContributionRegistration
from platform_sdk import ActionContribution, ToolbarContribution, ViewContribution
from ui.views import (
    ActivitiesView,
    FunctionalAssignmentsView,
    FunctionalExercisesView,
)


def rsc_contributions() -> tuple[ContributionRegistration, ...]:
    application_id = "rsc"
    return (
        ContributionRegistration(
            ContributionCategory.ACTION,
            application_id,
            30,
            ActionContribution(
                "action_activities",
                "Atividades",
                "classification",
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
            ActionContribution(
                "action_functional_assignments",
                "Interpretações funcionais",
                "classification",
                visible=False,
                enabled=False,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.ACTION,
            application_id,
            10,
            ActionContribution(
                "action_functional_exercises",
                "Exercícios funcionais",
                "classification",
                visible=False,
                enabled=False,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            30,
            ToolbarContribution("main", "action_activities"),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            20,
            ToolbarContribution(
                "main", "action_functional_assignments"
            ),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            application_id,
            10,
            ToolbarContribution(
                "main", "action_functional_exercises"
            ),
        ),
        ContributionRegistration(
            ContributionCategory.VIEW,
            application_id,
            30,
            ViewContribution(
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
            ViewContribution(
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
            ViewContribution(
                "functional_exercises",
                "functional_exercises_view",
                FunctionalExercisesView,
                "show_functional_exercises",
            ),
        ),
    )
