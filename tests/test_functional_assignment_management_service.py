from datetime import date
import unittest
from unittest.mock import Mock
from uuid import uuid4

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    SourceEvidenceReference,
)
from applications.rsc.services import (
    FunctionalAssignmentManagementError,
    FunctionalAssignmentManagementService,
)


def assignment():
    return FunctionalAssignmentEvidence(
        id=FunctionalAssignmentEvidenceId(str(uuid4())),
        person_id="person-1",
        source_evidence_reference=SourceEvidenceReference(
            str(uuid4())
        ),
        exercise_type_code="coordenacao",
        exercise_type_label="Coordenação",
        role="Coordenador",
        organization="Instituto",
        start_date=date(2024, 1, 1),
    )


class FunctionalAssignmentManagementServiceTests(unittest.TestCase):
    def setUp(self):
        self.item = assignment()
        self.repository = Mock()
        self.repository.get_by_id.return_value = self.item
        self.lookup = Mock()
        self.lookup.exists.return_value = True
        self.service = FunctionalAssignmentManagementService(
            self.repository,
            self.lookup,
        )

    def test_update_preserves_identity_source_and_status(self):
        self.repository.update.side_effect = lambda item: item

        updated = self.service.update(
            str(self.item.id),
            role="Diretor",
            organization="Campus",
        )

        self.assertEqual(updated.id, self.item.id)
        self.assertEqual(
            updated.source_evidence_reference,
            self.item.source_evidence_reference,
        )
        self.assertIs(
            updated.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )
        self.assertEqual(updated.role, "Diretor")

    def test_pipeline_is_explicit_raw_identified_linked(self):
        self.repository.update.side_effect = lambda item: item

        identified = self.service.advance(str(self.item.id))
        self.assertIs(
            identified.status,
            FunctionalAssignmentEvidenceStatus.IDENTIFIED,
        )
        self.repository.get_by_id.return_value = identified
        linked = self.service.advance(str(self.item.id))
        self.assertIs(
            linked.status,
            FunctionalAssignmentEvidenceStatus.LINKED,
        )

    def test_missing_source_blocks_mutation(self):
        self.lookup.exists.return_value = False

        with self.assertRaisesRegex(
            FunctionalAssignmentManagementError,
            "Evidence de origem",
        ):
            self.service.update(str(self.item.id), role="Diretor")

        self.repository.update.assert_not_called()

    def test_delete_uses_only_assignment_repository(self):
        self.repository.delete.return_value = self.item

        deleted = self.service.delete(str(self.item.id))

        self.assertIs(deleted, self.item)
        self.repository.delete.assert_called_once_with(self.item.id)


if __name__ == "__main__":
    unittest.main()
