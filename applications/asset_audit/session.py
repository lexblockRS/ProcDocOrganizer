"""Sessão própria e isolada da Asset Audit."""

from platform_sdk import SessionContext

from .models import Asset, Audit, Finding
from .services import AssetService, AuditService, FindingService


class AssetAuditSession:
    def __init__(
        self,
        context: SessionContext,
        asset_service: AssetService,
        audit_service: AuditService,
        finding_service: FindingService,
    ):
        if not isinstance(context, SessionContext):
            raise TypeError("context deve ser um SessionContext.")
        self.context = context
        self._asset_service = asset_service
        self._audit_service = audit_service
        self._finding_service = finding_service
        self.cache = {}
        self.settings = {"storage": "memory"}
        self.state = "created"

    @property
    def asset_service(self):
        self._ensure_available()
        return self._asset_service

    @property
    def audit_service(self):
        self._ensure_available()
        return self._audit_service

    @property
    def finding_service(self):
        self._ensure_available()
        return self._finding_service

    @property
    def is_active(self):
        return self.state == "active"

    @property
    def is_disposed(self):
        return self.state == "disposed"

    def activate(self):
        self._ensure_available()
        self.state = "active"

    def dispose(self):
        if self.is_disposed:
            return
        self.cache.clear()
        self.state = "disposed"

    def _ensure_available(self):
        if self.is_disposed:
            raise RuntimeError("AssetAuditSession já foi descartada.")


def create_demo_session(context: SessionContext) -> AssetAuditSession:
    assets = AssetService()
    audits = AuditService()
    findings = FindingService()

    created_assets = tuple(
        assets.add_asset(Asset(
            id=f"asset-{index:02d}",
            name=f"Asset {index:02d}",
            asset_type="equipment",
            owner="Asset Audit",
        ))
        for index in range(1, 13)
    )
    created_audits = tuple(
        audits.add_audit(Audit(
            id=f"audit-{index:02d}",
            title=f"Audit {index:02d}",
            status="open" if index <= 2 else "completed",
            asset_ids=tuple(
                item.id for item in created_assets[
                    (index - 1) * 3:index * 3
                ]
            ),
        ))
        for index in range(1, 5)
    )
    for index in range(1, 8):
        audit = created_audits[(index - 1) % len(created_audits)]
        findings.add_finding(Finding(
            id=f"finding-{index:02d}",
            audit_id=audit.id,
            title=f"Finding {index:02d}",
            severity="medium",
            status="pending" if index <= 2 else "resolved",
        ))

    return AssetAuditSession(context, assets, audits, findings)
