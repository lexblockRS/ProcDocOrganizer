"""Coordenação do fluxo de exercícios funcionais RSC."""

from PySide6.QtWidgets import QDialog, QInputDialog

from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.services import FunctionalExerciseManagementService
from presentation import (
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
)
from ui.dialogs import FunctionalExerciseDialog


class FunctionalExercisesController:
    """Expõe casos de uso existentes sem reproduzir regras de negócio."""

    def __init__(
        self,
        view,
        parent=None,
        dialog_factory=FunctionalExerciseDialog,
        assignment_navigation_requested=None,
        selection_store=None,
        notify=None,
        confirm_delete=None,
    ):
        self.view = view
        self.parent = parent
        self._dialog_factory = dialog_factory
        self._assignment_navigation_requested = (
            assignment_navigation_requested
        )
        self._selection_store = selection_store
        self._notify = notify or (lambda _kind, _message: None)
        self._confirm_delete = confirm_delete or (lambda _item: False)
        self._session = None
        self._selected = None
        self._management_service = None
        view.exercise_selected.connect(self.select)
        view.open_assignment_requested.connect(self.open_assignment)
        view.refresh_requested.connect(self.refresh)
        if hasattr(view, "new_requested"):
            view.new_requested.connect(self.create)
            view.edit_requested.connect(self.edit)
            view.delete_requested.connect(self.delete)
        if self._selection_store is not None:
            self._unsubscribe_selection = self._selection_store.subscribe(
                self._on_selection_changed
            )
        self.clear_session()

    def set_session(self, session) -> bool:
        self._session = (
            session
            if getattr(session, "rsc_session", None) is not None
            else None
        )
        self._selected = None
        self._management_service = (
            FunctionalExerciseManagementService(
                self._session.rsc_session.functional_exercise_repository,
                self._session.rsc_session
                .functional_assignment_evidence_repository,
            )
            if self._session is not None
            else None
        )
        return self.refresh()

    def clear_session(self):
        self._session = None
        self._selected = None
        self._management_service = None
        self._clear_selection()
        self.view.clear()

    def create(self, assignment_ids=None) -> bool:
        if self._session is None:
            return False
        if assignment_ids is None:
            references, accepted = QInputDialog.getText(
                self.parent,
                "Novo exercício funcional",
                "IDs das interpretações, separados por vírgula:",
            )
            if not accepted:
                self._notify("info", "Operação cancelada.")
                return False
            identifiers = tuple(
                item.strip()
                for item in references.split(",")
                if item.strip()
            )
        else:
            identifiers = tuple(assignment_ids)
        if not identifiers:
            self.view.show_error(
                "Selecione ao menos uma interpretação funcional."
            )
            self._notify(
                "error",
                "Selecione ao menos uma interpretação funcional.",
            )
            return False
        assignments = self._assignments(identifiers)
        if {item.id for item in assignments} != set(identifiers):
            self.view.show_error(
                "Uma interpretação selecionada não está mais disponível."
            )
            self._notify(
                "error",
                "Uma interpretação selecionada não está disponível.",
            )
            return False
        dialog = self._dialog_factory(assignments, self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            command = CreateFunctionalExerciseCommand(
                functional_assignment_evidence_ids=identifiers,
                **dialog.values(),
            )
            created = (
                self._session.rsc_session
                .create_functional_exercise_service.execute(command)
            )
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self._selected = created.id
        self.refresh()
        self.view.show_message("Exercício funcional criado com sucesso.")
        self._notify("success", "Exercício funcional criado.")
        return True

    def refresh(self) -> bool:
        if self._session is None:
            self.view.clear()
            return False
        self.view.show_loading()
        try:
            items = (
                self._session.rsc_session
                .list_functional_exercises_service.execute()
            )
        except Exception:
            self.view.show_error(
                "Não foi possível carregar os exercícios funcionais."
            )
            return False
        self.view.set_items(items)
        identifiers = {item.id for item in items}
        selected = (
            self._selected if self._selected in identifiers
            else (items[0].id if items else None)
        )
        if selected is None:
            self._selected = None
            self.view.set_details(None, ())
            return True
        return self.select(selected)

    def select(self, exercise_id) -> bool:
        if self._session is None:
            return False
        exercises = (
            self._session.rsc_session
            .list_functional_exercises_service.execute()
        )
        exercise = next(
            (item for item in exercises if item.id == exercise_id), None
        )
        if exercise is None:
            return False
        assignments = self._assignments(
            exercise.functional_assignment_evidence_ids
        )
        related = tuple(
            (
                assignment,
                self._session.evidence_service.get(
                    assignment.source_evidence_reference
                ),
            )
            for assignment in assignments
        )
        self._selected = exercise.id
        if self._selection_store is not None:
            self._selection_store.select(SelectionContext(
                SelectionIdentity(
                    SelectionKind.FUNCTIONAL_EXERCISE,
                    exercise.id,
                ),
                display_name=exercise.role,
            ))
        self.view.select_exercise(exercise.id)
        self.view.set_details(exercise, related)
        return True

    def edit(self) -> bool:
        exercise = self._current()
        if exercise is None or self._management_service is None:
            return False
        assignments = self._assignments(
            exercise.functional_assignment_evidence_ids
        )
        dialog = self._dialog_factory(assignments, self.parent)
        if hasattr(dialog, "fields"):
            values = {
                "person_id": exercise.person_id,
                "exercise_type_code": exercise.exercise_type_code,
                "exercise_type_label": exercise.exercise_type_label,
                "role": exercise.role,
                "context_organization": exercise.context_organization,
                "context_unit": exercise.context_unit or "",
                "context_reference": exercise.context_reference or "",
                "start_date": exercise.start_date.isoformat(),
                "end_date": (
                    exercise.end_date.isoformat()
                    if exercise.end_date else ""
                ),
            }
            for name, value in values.items():
                dialog.fields[name].setText(value)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            self._management_service.update(
                exercise.id,
                functional_assignment_evidence_ids=(
                    exercise.functional_assignment_evidence_ids
                ),
                **dialog.values(),
            )
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self.refresh()
        self._notify("success", "Exercício funcional atualizado.")
        return True

    def delete(self) -> bool:
        exercise = self._current()
        if (
            exercise is None
            or self._management_service is None
            or not self._confirm_delete(exercise)
        ):
            return False
        try:
            self._management_service.delete(exercise.id)
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self._selected = None
        self._clear_selection()
        self.refresh()
        self._notify("success", "Exercício funcional removido.")
        return True

    def _current(self):
        if self._session is None or self._selected is None:
            return None
        return next(
            (
                item for item in self._session.rsc_session
                .list_functional_exercises_service.execute()
                if item.id == self._selected
            ),
            None,
        )

    def _clear_selection(self):
        if self._selection_store is None:
            return
        identity = self._selection_store.snapshot.selection.identity
        if identity.kind is SelectionKind.FUNCTIONAL_EXERCISE:
            self._selection_store.clear()

    def _on_selection_changed(self, snapshot):
        identity = snapshot.selection.identity
        if identity.kind is SelectionKind.FUNCTIONAL_EXERCISE:
            if identity.identifier != self._selected:
                self.select(identity.identifier)
        elif self._selected is not None:
            self._selected = None
            self.view.select_exercise(None)

    def open_assignment(self, assignment_id) -> bool:
        if (
            self._session is None
            or self._assignment_navigation_requested is None
        ):
            return False
        if not any(
            item.id == assignment_id
            for item in self._assignments((assignment_id,))
        ):
            self.view.show_error(
                "A interpretação relacionada não está mais disponível."
            )
            return False
        return bool(
            self._assignment_navigation_requested(assignment_id)
        )

    def _assignments(self, identifiers):
        wanted = set(identifiers)
        return tuple(
            item for item in (
                self._session.rsc_session
                .list_functional_assignment_evidences_service.execute()
            )
            if item.id in wanted
        )

    @staticmethod
    def _message(error):
        if isinstance(error, (ValueError, TypeError)):
            return f"Revise os dados informados: {error}"
        if isinstance(error, LookupError):
            return str(error)
        return "Não foi possível criar o exercício funcional."
