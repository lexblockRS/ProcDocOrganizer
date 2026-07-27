"""Coordenação da tela de atividades."""

from PySide6.QtWidgets import QDialog, QMessageBox

from applications.rsc.commands import CreateActivityCommand
from ui.dialogs import ActivityDialog

from .projections import ActivitiesProjection, ActivitiesViewState
from .service import ActivitiesService


class ActivitiesController:
    """Integra lifecycle, intenções da view e serviço de leitura."""

    ERROR_MESSAGE = "Não foi possível carregar as atividades do projeto."

    def __init__(
        self,
        view,
        service_factory=ActivitiesService,
        parent=None,
        dialog_factory=ActivityDialog,
        assignment_navigation_requested=None,
        exercise_navigation_requested=None,
    ) -> None:
        self.view = view
        self._service_factory = service_factory
        self._service = None
        self._project_name = None
        self._selected_activity_id = None
        self._session = None
        self._parent = parent
        self._dialog_factory = dialog_factory
        self._assignment_navigation_requested = (
            assignment_navigation_requested
        )
        self._exercise_navigation_requested = exercise_navigation_requested
        view.refresh_requested.connect(self.refresh)
        view.retry_requested.connect(self.refresh)
        view.activity_selected.connect(self.select_activity)
        if hasattr(view, "open_assignment_requested"):
            view.open_assignment_requested.connect(self.open_assignment)
        if hasattr(view, "open_exercise_requested"):
            view.open_exercise_requested.connect(self.open_exercise)
        self.clear_session()

    def set_session(self, session) -> bool:
        self._selected_activity_id = None
        self._session = session
        self._project_name = session.project.project_name
        rsc_session = getattr(session, "rsc_session", None)
        if rsc_session is None:
            self._session = None
            self._service = None
            self.view.set_projection(ActivitiesProjection(
                state=ActivitiesViewState.ERROR,
                project_name=self._project_name,
                error_message="O projeto atual não oferece atividades RSC.",
            ))
            return False
        self._service = self._service_factory(
            rsc_session.activity_repository,
            self._project_name,
            getattr(rsc_session, "functional_exercise_repository", None),
            getattr(
                rsc_session,
                "functional_assignment_evidence_repository",
                None,
            ),
            getattr(session, "evidence_service", None),
        )
        return self.refresh()

    def clear_session(self) -> None:
        self._service = None
        self._project_name = None
        self._selected_activity_id = None
        self._session = None
        self.view.set_projection(ActivitiesProjection())

    def refresh(self) -> bool:
        if self._service is None:
            self.view.set_projection(ActivitiesProjection())
            return False
        self.view.set_projection(ActivitiesProjection(
            state=ActivitiesViewState.LOADING,
            project_name=self._project_name,
        ))
        try:
            projection = self._service.build(
                self._selected_activity_id
            )
        except Exception:
            self.view.set_projection(ActivitiesProjection(
                state=ActivitiesViewState.ERROR,
                project_name=self._project_name,
                error_message=self.ERROR_MESSAGE,
            ))
            return False
        self._selected_activity_id = projection.selected_activity_id
        self.view.set_projection(projection)
        return True

    def select_activity(self, activity_id: str) -> bool:
        if self._service is None:
            return False
        self._selected_activity_id = activity_id
        return self.refresh()

    def create(self, exercise_ids=(), assignment_ids=()) -> bool:
        if self._session is None:
            return False
        identifiers = tuple(exercise_ids)
        assignment_identifiers = tuple(assignment_ids)
        if not identifiers and not assignment_identifiers:
            return False
        dialog = self._dialog_factory(
            len(identifiers) + len(assignment_identifiers),
            self._parent,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        try:
            created = (
                self._session.rsc_session.create_activity_service.execute(
                    CreateActivityCommand(
                        functional_exercise_ids=identifiers,
                        functional_assignment_evidence_ids=(
                            assignment_identifiers
                        ),
                        **dialog.values(),
                    )
                )
            )
        except Exception as exc:
            QMessageBox.warning(
                self._parent,
                "Atividade funcional",
                f"Não foi possível criar a atividade: {exc}",
            )
            return False
        self._selected_activity_id = created.activity_id
        return self.refresh()

    def open_assignment(self, assignment_id):
        if self._assignment_navigation_requested is None:
            return False
        return bool(
            self._assignment_navigation_requested(assignment_id)
        )

    def open_exercise(self, exercise_id):
        if self._exercise_navigation_requested is None:
            return False
        opened = bool(self._exercise_navigation_requested(exercise_id))
        if not opened:
            QMessageBox.information(
                self._parent,
                "Exercício funcional indisponível",
                "O exercício funcional referenciado não pôde ser localizado.",
            )
        return opened
