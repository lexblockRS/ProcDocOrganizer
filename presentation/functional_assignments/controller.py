"""Coordenação do primeiro fluxo funcional RSC."""

from datetime import date

from PySide6.QtWidgets import QDialog, QMessageBox

from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from ui.dialogs import FunctionalAssignmentDialog


class FunctionalAssignmentsController:
    """Liga Evidence aos casos de uso RSC sem conter regras de domínio."""

    def __init__(
        self,
        view,
        parent=None,
        dialog_factory=FunctionalAssignmentDialog,
        evidence_navigation_requested=None,
    ) -> None:
        self.view = view
        self.parent = parent
        self._dialog_factory = dialog_factory
        self._evidence_navigation_requested = evidence_navigation_requested
        self._session = None
        self._selected = None
        view.assignment_selected.connect(self.select)
        view.open_source_requested.connect(self.open_source)
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

    def clear_session(self) -> None:
        self._session = None
        self._selected = None
        self.view.clear()

    def create_from_evidence(self, evidence) -> bool:
        if self._session is None or evidence is None:
            return False
        dialog = self._dialog_factory(evidence, self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        try:
            values = dialog.values()
            command = CreateFunctionalAssignmentEvidenceCommand(
                source_evidence_reference=evidence.id,
                start_date=self._optional_date(values.pop("start_date")),
                end_date=self._optional_date(values.pop("end_date")),
                **values,
            )
            created = (
                self._session.rsc_session
                .create_functional_assignment_evidence_service
                .execute(command)
            )
        except Exception as exc:
            QMessageBox.warning(
                self.parent,
                "Interpretação funcional",
                self._message(exc),
            )
            return False
        self._selected = created.id
        self.refresh()
        self.view.show_message("Interpretação funcional criada com sucesso.")
        return True

    def refresh(self) -> bool:
        if self._session is None:
            self.view.clear()
            return False
        try:
            items = (
                self._session.rsc_session
                .list_functional_assignment_evidences_service.execute()
            )
        except Exception:
            self.view.show_error(
                "Não foi possível carregar as interpretações funcionais."
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
            self.view.set_details(None, None, self._session.project.project_name)
            return True
        return self.select(selected)

    def select(self, assignment_id: str) -> bool:
        if self._session is None:
            return False
        items = (
            self._session.rsc_session
            .list_functional_assignment_evidences_service.execute()
        )
        assignment = next(
            (item for item in items if item.id == assignment_id), None
        )
        if assignment is None:
            return False
        evidence = self._session.evidence_service.get(
            assignment.source_evidence_reference
        )
        self._selected = assignment.id
        self.view.select_assignment(assignment.id)
        self.view.set_details(
            assignment, evidence, self._session.project.project_name
        )
        return True

    def open_source(self) -> bool:
        if self._session is None or self._selected is None:
            return False
        items = (
            self._session.rsc_session
            .list_functional_assignment_evidences_service.execute()
        )
        assignment = next(
            (item for item in items if item.id == self._selected), None
        )
        if assignment is None or self._evidence_navigation_requested is None:
            return False
        return bool(self._evidence_navigation_requested(
            assignment.source_evidence_reference
        ))

    @staticmethod
    def _optional_date(value: str):
        normalized = value.strip()
        return date.fromisoformat(normalized) if normalized else None

    @staticmethod
    def _message(error: Exception) -> str:
        if isinstance(error, ValueError):
            return f"Revise os dados informados: {error}"
        if isinstance(error, LookupError):
            return "A Evidence de origem não está mais disponível."
        return "Não foi possível criar a interpretação funcional."
