"""Coordenação do fluxo de exercícios funcionais RSC."""

from PySide6.QtWidgets import QDialog, QMessageBox

from applications.rsc.commands import CreateFunctionalExerciseCommand
from ui.dialogs import FunctionalExerciseDialog


class FunctionalExercisesController:
    """Expõe casos de uso existentes sem reproduzir regras de negócio."""

    def __init__(
        self,
        view,
        parent=None,
        dialog_factory=FunctionalExerciseDialog,
        assignment_navigation_requested=None,
    ):
        self.view = view
        self.parent = parent
        self._dialog_factory = dialog_factory
        self._assignment_navigation_requested = (
            assignment_navigation_requested
        )
        self._session = None
        self._selected = None
        view.exercise_selected.connect(self.select)
        view.open_assignment_requested.connect(self.open_assignment)
        view.refresh_requested.connect(self.refresh)
        self.clear_session()

    def set_session(self, session) -> bool:
        self._session = (
            session
            if getattr(session, "rsc_session", None) is not None
            else None
        )
        self._selected = None
        return self.refresh()

    def clear_session(self):
        self._session = None
        self._selected = None
        self.view.clear()

    def create(self, assignment_ids) -> bool:
        if self._session is None:
            return False
        identifiers = tuple(assignment_ids)
        if not identifiers:
            self.view.show_error(
                "Selecione ao menos uma interpretação funcional."
            )
            return False
        assignments = self._assignments(identifiers)
        if {item.id for item in assignments} != set(identifiers):
            self.view.show_error(
                "Uma interpretação selecionada não está mais disponível."
            )
            return False
        dialog = self._dialog_factory(assignments, self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
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
            QMessageBox.warning(
                self.parent,
                "Exercício funcional",
                self._message(exc),
            )
            return False
        self._selected = created.id
        self.refresh()
        self.view.show_message("Exercício funcional criado com sucesso.")
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
        self.view.select_exercise(exercise.id)
        self.view.set_details(exercise, related)
        return True

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
