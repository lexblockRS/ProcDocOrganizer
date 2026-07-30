"""Coordenação do primeiro fluxo funcional RSC."""

from datetime import date

from PySide6.QtWidgets import QDialog, QInputDialog

from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.services import (
    FunctionalAssignmentManagementService,
)
from presentation import (
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
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
        selection_store=None,
        notify=None,
        confirm_delete=None,
    ) -> None:
        self.view = view
        self.parent = parent
        self._dialog_factory = dialog_factory
        self._evidence_navigation_requested = evidence_navigation_requested
        self._selection_store = selection_store
        self._notify = notify or (lambda _kind, _message: None)
        self._confirm_delete = confirm_delete or (lambda _item: False)
        self._session = None
        self._selected = None
        self._management_service = None
        view.assignment_selected.connect(self.select)
        view.open_source_requested.connect(self.open_source)
        view.refresh_requested.connect(self.refresh)
        if hasattr(view, "new_requested"):
            view.new_requested.connect(self.create)
            view.edit_requested.connect(self.edit)
            view.delete_requested.connect(self.delete)
            view.advance_requested.connect(self.advance)
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
        if self._session is not None:
            self._management_service = FunctionalAssignmentManagementService(
                self._session.rsc_session
                .functional_assignment_evidence_repository,
                self._session.evidence_service,
            )
        return self.refresh()

    def clear_session(self) -> None:
        self._session = None
        self._selected = None
        self._management_service = None
        self._clear_selection()
        self.view.clear()

    def create(self) -> bool:
        if self._session is None:
            return False
        reference, accepted = QInputDialog.getText(
            self.parent,
            "Nova interpretação funcional",
            "ID da Evidence de origem:",
        )
        if not accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            evidence = self._session.evidence_service.get(reference.strip())
        except (TypeError, ValueError):
            evidence = None
        if evidence is None:
            self._notify("error", "A Evidence de origem não foi localizada.")
            return False
        return self.create_from_evidence(evidence)

    def create_from_evidence(self, evidence) -> bool:
        if self._session is None or evidence is None:
            return False
        dialog = self._dialog_factory(evidence, self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
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
            self._notify("error", self._message(exc))
            return False
        self._selected = created.id
        self.refresh()
        self.view.show_message("Interpretação funcional criada com sucesso.")
        self._notify("success", "Interpretação funcional criada.")
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
        if self._selection_store is not None:
            self._selection_store.select(SelectionContext(
                SelectionIdentity(
                    SelectionKind.FUNCTIONAL_ASSIGNMENT,
                    assignment.id,
                ),
                display_name=assignment.role,
            ))
        self.view.select_assignment(assignment.id)
        self.view.set_details(
            assignment, evidence, self._session.project.project_name
        )
        return True

    def edit(self) -> bool:
        assignment = self._current()
        if assignment is None or self._management_service is None:
            return False
        evidence = self._session.evidence_service.get(
            assignment.source_evidence_reference
        )
        if evidence is None:
            self._notify("error", "A Evidence de origem não está disponível.")
            return False
        dialog = self._dialog_factory(evidence, self.parent)
        if hasattr(dialog, "fields"):
            for name, field in dialog.fields.items():
                value = getattr(assignment, name, None)
                if isinstance(value, date):
                    value = value.isoformat()
                field.setText(str(value) if value is not None else "")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._notify("info", "Operação cancelada.")
            return False
        try:
            values = dialog.values()
            values["start_date"] = self._optional_date(
                values["start_date"]
            )
            values["end_date"] = self._optional_date(values["end_date"])
            self._management_service.update(assignment.id, **values)
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self.refresh()
        self._notify("success", "Interpretação funcional atualizada.")
        return True

    def advance(self) -> bool:
        assignment = self._current()
        if assignment is None or self._management_service is None:
            return False
        try:
            advanced = self._management_service.advance(assignment.id)
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self._selected = str(advanced.id)
        self.refresh()
        self._notify(
            "success",
            f"Estado alterado para {advanced.status.value.upper()}.",
        )
        return True

    def delete(self) -> bool:
        assignment = self._current()
        if (
            assignment is None
            or self._management_service is None
            or not self._confirm_delete(assignment)
        ):
            return False
        try:
            self._management_service.delete(assignment.id)
        except Exception as exc:
            self._notify("error", self._message(exc))
            return False
        self._selected = None
        self._clear_selection()
        self.refresh()
        self._notify("success", "Interpretação funcional removida.")
        return True

    def _current(self):
        if self._session is None or self._selected is None:
            return None
        return next(
            (
                item for item in self._session.rsc_session
                .list_functional_assignment_evidences_service.execute()
                if item.id == self._selected
            ),
            None,
        )

    def _clear_selection(self):
        if self._selection_store is None:
            return
        identity = self._selection_store.snapshot.selection.identity
        if identity.kind is SelectionKind.FUNCTIONAL_ASSIGNMENT:
            self._selection_store.clear()

    def _on_selection_changed(self, snapshot):
        identity = snapshot.selection.identity
        if identity.kind is SelectionKind.FUNCTIONAL_ASSIGNMENT:
            if identity.identifier != self._selected:
                self.select(identity.identifier)
        elif self._selected is not None:
            self._selected = None
            self.view.select_assignment(None)

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
