from ..models import Finding


class FindingService:
    def __init__(self):
        self._items = {}

    def list_findings(self):
        return tuple(self._items.values())

    def get_finding(self, finding_id):
        try:
            return self._items[finding_id]
        except KeyError as exc:
            raise KeyError(
                f"Finding não encontrado: {finding_id}."
            ) from exc

    def add_finding(self, finding):
        if not isinstance(finding, Finding):
            raise TypeError("finding deve ser um Finding.")
        if finding.id in self._items:
            raise ValueError(f"Finding já cadastrado: {finding.id}.")
        self._items[finding.id] = finding
        return finding

    def count_findings(self):
        return len(self._items)

    def count_pending_findings(self):
        return sum(
            item.status == "pending" for item in self._items.values()
        )
