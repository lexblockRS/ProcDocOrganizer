"""Coordenação da tela de atividades."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox

from applications.rsc.services import ActivityManagementService
from presentation import (
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
)
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
        selection_store=None,
        notify=None,
        confirm_delete=None,
        confirm_unsaved=None,
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
        self._selection_store = selection_store
        self._notify = notify or (lambda _kind, _message: None)
        self._confirm_delete = confirm_delete or (lambda _item: False)
        self._confirm_unsaved = confirm_unsaved or (lambda: "cancel")
        self._management_service = None
        view.refresh_requested.connect(self.refresh)
        view.retry_requested.connect(self.refresh)
        view.activity_selected.connect(self.select_activity)
        if hasattr(view, "open_assignment_requested"):
            view.open_assignment_requested.connect(self.open_assignment)
        if hasattr(view, "open_exercise_requested"):
            view.open_exercise_requested.connect(self.open_exercise)
        if hasattr(view, "create_requested"):
            view.create_requested.connect(self.create_activity)
            view.save_requested.connect(self.save_activity)
            view.cancel_requested.connect(self.cancel_edit)
            view.delete_requested.connect(self.delete_activity)
        if self._selection_store is not None:
            self._unsubscribe_selection = self._selection_store.subscribe(
                self._on_selection_changed
            )
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
        self._management_service = ActivityManagementService(
            rsc_session.activity_repository,
            getattr(rsc_session, "functional_exercise_repository", None),
        )
        return self.refresh()

    def clear_session(self) -> None:
        self._service = None
        self._project_name = None
        self._selected_activity_id = None
        self._session = None
        self._management_service = None
        self.view.set_projection(ActivitiesProjection())

    def refresh(self, force=False) -> bool:
        if not force and not self.can_leave():
            return False
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
        if self._selection_store is not None:
            if projection.selected_activity is not None:
                details = projection.selected_activity
                self._selection_store.select(
                    SelectionContext(
                        SelectionIdentity(
                            SelectionKind.ACTIVITY,
                            details.activity_id,
                        ),
                        display_name=details.description,
                    )
                )
            else:
                current = (
                    self._selection_store.snapshot.selection.identity
                )
                if current.kind is SelectionKind.ACTIVITY:
                    self._selection_store.clear()
        return True

    def select_activity(self, activity_id: str) -> bool:
        if self._service is None:
            return False
        if (
            activity_id != self._selected_activity_id
            and not self.can_leave()
        ):
            self._restore_view_selection()
            return False
        if self._selection_store is not None:
            projection = self.view._projection
            item = next(
                (
                    value for value in projection.items
                    if value.activity_id == activity_id
                ),
                None,
            )
            if item is None:
                return False
            self._selected_activity_id = activity_id
            self._selection_store.select(
                SelectionContext(
                    SelectionIdentity(
                        SelectionKind.ACTIVITY,
                        activity_id,
                    ),
                    display_name=item.description,
                )
            )
        else:
            self._selected_activity_id = activity_id
        return self.refresh()

    def create_activity(self) -> bool:
        if self._management_service is None:
            return False
        references, accepted = QInputDialog.getText(
            self._parent,
            "Nova Activity",
            "IDs dos FunctionalExercises, separados por vírgula:",
        )
        if not accepted:
            self._notify("info", "Operação cancelada.")
            return False
        exercise_ids = tuple(
            item.strip()
            for item in references.split(",")
            if item.strip()
        )
        if not exercise_ids:
            self._notify(
                "error",
                "Selecione ao menos um FunctionalExercise.",
            )
            return False
        dialog = self._dialog_factory(len(exercise_ids), self._parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            created = self._management_service.create(
                dialog.values()["description"],
                exercise_ids,
            )
        except Exception as exc:
            self._notify(
                "error",
                f"Falha ao criar Activity: {exc}",
            )
            return False
        self._selected_activity_id = created.activity_id
        if self._selection_store is not None:
            self._selection_store.select(
                SelectionContext(
                    SelectionIdentity(
                        SelectionKind.ACTIVITY,
                        created.activity_id,
                    ),
                    display_name=created.description,
                )
            )
        self.refresh(force=True)
        self._notify("success", "Activity criada.")
        return True

    def save_activity(
        self,
        description: str,
        state: str | None = None,
    ) -> bool:
        if (
            self._management_service is None
            or self._selected_activity_id is None
        ):
            return False
        try:
            current_state = self.view._projection.selected_activity.state
            updated = self._management_service.update(
                self._selected_activity_id,
                description,
                state or current_state,
            )
        except Exception as exc:
            self.view.show_edit_error(str(exc))
            self._notify(
                "error",
                f"Falha de persistência: {exc}",
            )
            return False
        self.view.finish_edit()
        if self._selection_store is not None:
            self._selection_store.select(
                SelectionContext(
                    SelectionIdentity(
                        SelectionKind.ACTIVITY,
                        updated.activity_id,
                    ),
                    display_name=updated.description,
                )
            )
        self.refresh(force=True)
        self._notify("success", "Activity atualizada.")
        return True

    def cancel_edit(self) -> bool:
        if not self.view.is_editing:
            return False
        self.view.cancel_edit()
        self._notify("info", "Operação cancelada.")
        return True

    def delete_activity(self) -> bool:
        if (
            self._management_service is None
            or self._selected_activity_id is None
            or not self.can_leave()
        ):
            return False
        details = self.view._projection.selected_activity
        if details is None or not self._confirm_delete(details):
            self._notify("info", "Operação cancelada.")
            return False
        try:
            self._management_service.delete(
                self._selected_activity_id
            )
        except Exception as exc:
            self._notify(
                "error",
                f"Falha de persistência: {exc}",
            )
            return False
        self._selected_activity_id = None
        if self._selection_store is not None:
            self._selection_store.clear()
        self.refresh(force=True)
        self._notify("success", "Activity removida.")
        return True

    def can_leave(self) -> bool:
        if not getattr(self.view, "has_unsaved_changes", False):
            return True
        decision = self._confirm_unsaved()
        if decision == "save":
            return self.save_activity(
                self.view.description_editor.text(),
                self.view.state_editor.currentData(),
            )
        if decision == "discard":
            self.cancel_edit()
            return True
        return False

    def _restore_view_selection(self) -> None:
        for row in range(self.view.activity_list.count()):
            item = self.view.activity_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == self._selected_activity_id:
                self.view.activity_list.blockSignals(True)
                self.view.activity_list.setCurrentItem(item)
                self.view.activity_list.blockSignals(False)
                return

    def _on_selection_changed(self, snapshot) -> None:
        identity = snapshot.selection.identity
        if identity.kind is not SelectionKind.ACTIVITY:
            return
        if identity.identifier == self._selected_activity_id:
            return
        self._selected_activity_id = identity.identifier
        self.refresh(force=True)

    def create(self, exercise_ids=(), assignment_ids=()) -> bool:
        if self._session is None:
            return False
        identifiers = tuple(exercise_ids)
        if assignment_ids:
            self._notify(
                "error",
                "Activity aceita somente referências de FunctionalExercise.",
            )
            return False
        if not identifiers:
            return False
        dialog = self._dialog_factory(
            len(identifiers),
            self._parent,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            created = self._management_service.create(
                dialog.values()["description"],
                identifiers,
            )
        except Exception as exc:
            self._notify(
                "error",
                f"Não foi possível criar a Activity: {exc}",
            )
            return False
        self._selected_activity_id = created.activity_id
        if self._selection_store is not None:
            self._selection_store.select(SelectionContext(
                SelectionIdentity(
                    SelectionKind.ACTIVITY,
                    created.activity_id,
                ),
                display_name=created.description,
            ))
        self.refresh(force=True)
        self._notify("success", "Activity criada.")
        return True

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
