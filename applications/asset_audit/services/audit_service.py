from ..models import Audit


class AuditService:
    def __init__(self):
        self._items = {}

    def list_audits(self):
        return tuple(self._items.values())

    def get_audit(self, audit_id):
        try:
            return self._items[audit_id]
        except KeyError as exc:
            raise KeyError(f"Audit não encontrada: {audit_id}.") from exc

    def add_audit(self, audit):
        if not isinstance(audit, Audit):
            raise TypeError("audit deve ser uma Audit.")
        if audit.id in self._items:
            raise ValueError(f"Audit já cadastrada: {audit.id}.")
        self._items[audit.id] = audit
        return audit

    def count_audits(self):
        return len(self._items)

    def count_open_audits(self):
        return sum(item.status == "open" for item in self._items.values())
