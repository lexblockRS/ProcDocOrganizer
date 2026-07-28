from datetime import date
from decimal import Decimal
import unittest
from uuid import UUID

from applications.rsc.catalogs import OfficialRscCatalog
from applications.rsc.domain import (
    ActivityStatus,
    DocumentStatus,
    EvidenceStatus,
    MeasurementUnit,
    RscActivity,
    RscDocument,
    RscEvidence,
    RscProcess,
    RscProcessStatus,
    criterion_id,
    requirement_id,
)
from applications.rsc.services import (
    RscActivityService,
    RscEvidenceService,
    RscProcessService,
    RscScoringService,
    RscValidationService,
)
from applications.rsc.application import RscApplication


class OfficialCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = OfficialRscCatalog()

    def test_has_exact_official_shape_and_unique_ids(self):
        requirements = self.catalog.list_requirements()
        criteria = self.catalog.list_criteria()

        self.assertEqual(len(requirements), 6)
        self.assertEqual(len(criteria), 55)
        self.assertEqual(
            [
                len(self.catalog.list_criteria_by_requirement(item.id))
                for item in requirements
            ],
            [10, 11, 3, 8, 4, 19],
        )
        self.assertEqual(len({item.id for item in criteria}), 55)
        self.assertEqual(
            [item.number for item in requirements], [1, 2, 3, 4, 5, 6]
        )

    def test_ids_order_units_and_decimal_points_are_stable(self):
        criteria = self.catalog.list_criteria()

        self.assertEqual(criteria[0].id, "rsc.criterion.1.1")
        self.assertEqual(criteria[-1].id, "rsc.criterion.6.19")
        self.assertEqual(
            self.catalog.get_criterion(criterion_id(1, 7)).points_per_unit,
            Decimal("1.5"),
        )
        self.assertEqual(
            self.catalog.get_criterion(criterion_id(1, 2)).points_per_unit,
            Decimal("4.5"),
        )
        self.assertEqual(
            self.catalog.get_criterion(criterion_id(1, 9)).points_per_unit,
            Decimal("7.5"),
        )
        self.assertEqual(
            self.catalog.get_criterion(criterion_id(6, 16)).points_per_unit,
            Decimal("3.5"),
        )
        self.assertEqual(
            self.catalog.get_criterion(criterion_id(6, 19)).measurement_unit,
            MeasurementUnit.MONTH,
        )

    def test_requirement_five_has_exact_titular_substituto_variants(self):
        expected = (("9", "4.5"), ("7.5", "3"), ("4.5", "1.5"), ("3", "1"))
        criteria = self.catalog.list_criteria_by_requirement(
            requirement_id(5)
        )

        self.assertEqual(
            tuple(
                tuple(str(variant.points_per_unit) for variant in item.score_variants)
                for item in criteria
            ),
            expected,
        )
        self.assertTrue(all(item.points_per_unit is None for item in criteria))

    def test_catalog_queries_are_read_only_and_reject_unknown_ids(self):
        first = self.catalog.list_criteria()
        self.assertIs(first, self.catalog.list_criteria())
        with self.assertRaises(KeyError):
            self.catalog.get_criterion("rsc.criterion.9.9")
        with self.assertRaises(AttributeError):
            first.append(first[0])


class DomainModelTests(unittest.TestCase):
    def test_process_uuid_dates_lifecycle_and_collections(self):
        process = RscProcess("Pessoa", "Instituição")
        activity = RscActivity(
            criterion_id(1, 1), "Conselho", Decimal("2")
        )
        before = process.updated_at

        UUID(process.id)
        self.assertIsNotNone(process.created_at.utcoffset())
        self.assertEqual(process.status, RscProcessStatus.DRAFT)
        process.add_activity(activity)
        process.attach_document("document-1")
        process.mark_in_preparation()

        self.assertEqual(process.get_activity(activity.id), activity)
        self.assertGreaterEqual(process.updated_at, before)
        self.assertEqual(process.status, RscProcessStatus.IN_PREPARATION)
        with self.assertRaises(ValueError):
            process.add_activity(activity)
        with self.assertRaises(ValueError):
            process.attach_document("document-1")

    def test_activity_validates_quantity_dates_and_evidence_duplicates(self):
        with self.assertRaises(ValueError):
            RscActivity(criterion_id(1, 1), "Inválida", 0)
        with self.assertRaises(ValueError):
            RscActivity(
                criterion_id(1, 1),
                "Inválida",
                1,
                start_date=date(2025, 2, 1),
                end_date=date(2025, 1, 1),
            )
        with self.assertRaises(ValueError):
            RscActivity(
                criterion_id(1, 1),
                "Inválida",
                1,
                evidence_ids=("e1", "e1"),
            )

    def test_document_is_passive_and_evidence_requires_documents(self):
        document = RscDocument(
            "ato.pdf",
            original_path="origem/ato.pdf",
            stored_path="acervo/ato.pdf",
            status=DocumentStatus.AVAILABLE,
        )
        self.assertEqual(document.file_name, "ato.pdf")
        with self.assertRaises(ValueError):
            RscDocument("")
        with self.assertRaises(ValueError):
            RscEvidence("activity-1", (), "Comprovação")

    def test_evidence_links_are_many_to_many_and_preserve_status(self):
        first = RscEvidence(
            "activity-1", ("document-1",), "Primeira"
        )
        second = RscEvidence(
            "activity-2",
            ("document-1", "document-2"),
            "Segunda",
            status=EvidenceStatus.ACCEPTED,
            justification="Conferida",
        )
        self.assertIn("document-1", first.document_ids)
        self.assertIn("document-1", second.document_ids)
        self.assertEqual(second.justification, "Conferida")
        with self.assertRaises(ValueError):
            RscEvidence(
                "activity-1", ("document-1", "document-1"), "Duplicada"
            )


class DomainServiceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = OfficialRscCatalog()
        self.processes = RscProcessService()
        self.activities = RscActivityService(self.catalog)
        self.evidence = RscEvidenceService()
        self.scoring = RscScoringService(self.catalog)
        self.validation = RscValidationService(self.catalog)
        self.process = self.processes.create_process(
            applicant_name="Pessoa", institution="Instituição"
        )

    def test_process_service_is_isolated_in_memory(self):
        self.assertEqual(self.processes.count_processes(), 1)
        self.assertEqual(
            self.processes.get_process(self.process.id), self.process
        )
        with self.assertRaises(ValueError):
            self.processes.add_process(self.process)
        self.processes.remove_process(self.process.id)
        self.assertEqual(self.processes.list_processes(), ())

    def test_activity_service_validates_catalog_and_variants(self):
        common = self.activities.create_activity(
            criterion_id=criterion_id(1, 1),
            title="Conselho",
            quantity=1,
        )
        titular_id = f"{criterion_id(5, 1)}.titular"
        variant = self.activities.create_activity(
            criterion_id=criterion_id(5, 1),
            title="Direção",
            quantity=1,
            score_variant_id=titular_id,
        )
        self.activities.add_activity(self.process, common)
        self.activities.add_activity(self.process, variant)

        self.assertEqual(
            len(
                self.activities.list_activities_by_requirement(
                    self.process, requirement_id(5)
                )
            ),
            1,
        )
        with self.assertRaises(KeyError):
            self.activities.create_activity(
                criterion_id="inexistente", title="X", quantity=1
            )
        with self.assertRaises(ValueError):
            self.activities.create_activity(
                criterion_id=criterion_id(5, 1),
                title="Sem variante",
                quantity=1,
            )

    def test_evidence_service_validates_activity_and_links(self):
        activity = self.activities.create_activity(
            criterion_id=criterion_id(1, 1),
            title="Conselho",
            quantity=1,
        )
        evidence = self.evidence.create_evidence(
            activity_id=activity.id,
            document_ids=("d1",),
            description="Ato",
        )
        linked = self.evidence.add_evidence(activity, evidence)
        linked_evidence = self.evidence.link_document(evidence, "d2")

        self.assertEqual(linked.evidence_ids, (evidence.id,))
        self.assertEqual(linked_evidence.document_ids, ("d1", "d2"))
        self.assertEqual(self.evidence.list_evidence(linked), (linked_evidence,))
        with self.assertRaises(ValueError):
            self.evidence.add_evidence(
                activity,
                RscEvidence("outra", ("d1",), "Incompatível"),
            )

    def test_scoring_is_decimal_pure_deterministic_and_excludes(self):
        activities = (
            self.activities.create_activity(
                criterion_id=criterion_id(1, 7),
                title="Mandato",
                quantity=2,
            ),
            self.activities.create_activity(
                criterion_id=criterion_id(3, 1),
                title="Prêmio",
                quantity=1,
            ),
            self.activities.create_activity(
                criterion_id=criterion_id(5, 1),
                title="Direção",
                quantity=1,
                score_variant_id=f"{criterion_id(5, 1)}.substituto",
            ),
            self.activities.create_activity(
                criterion_id=criterion_id(6, 1),
                title="Patente",
                quantity=1,
                status=ActivityStatus.EXCLUDED,
            ),
        )
        for activity in activities:
            self.activities.add_activity(self.process, activity)
        before = self.process.list_activities()

        first = self.scoring.calculate_process(self.process)
        second = self.scoring.calculate_process(self.process)

        self.assertEqual(first.total_score, Decimal("27.5"))
        self.assertEqual(first.total_score, second.total_score)
        self.assertEqual(self.process.list_activities(), before)
        excluded = self.scoring.calculate_activity(activities[-1])
        self.assertEqual(excluded.raw_score, Decimal("30"))
        self.assertEqual(excluded.applied_score, Decimal("0"))

    def test_scoring_covers_official_units_values_and_variants(self):
        samples = (
            (criterion_id(1, 2), None, "4.5"),
            (criterion_id(2, 1), None, "7.5"),
            (criterion_id(1, 10), None, "4.5"),
            (criterion_id(2, 7), None, "3"),
            (criterion_id(1, 7), None, "1.5"),
            (criterion_id(6, 19), None, "1"),
            (criterion_id(3, 1), None, "20"),
            (criterion_id(6, 1), None, "30"),
            (
                criterion_id(5, 1),
                f"{criterion_id(5, 1)}.titular",
                "9",
            ),
            (
                criterion_id(5, 1),
                f"{criterion_id(5, 1)}.substituto",
                "4.5",
            ),
        )
        for index, (criterion, variant, expected) in enumerate(samples):
            with self.subTest(criterion=criterion, variant=variant):
                activity = self.activities.create_activity(
                    criterion_id=criterion,
                    title=f"Atividade {index}",
                    quantity=1,
                    score_variant_id=variant,
                )
                score = self.scoring.calculate_activity(activity)
                self.assertEqual(score.raw_score, Decimal(expected))

        duplicate_criterion = criterion_id(2, 1)
        for index in range(2):
            self.activities.add_activity(
                self.process,
                self.activities.create_activity(
                    criterion_id=duplicate_criterion,
                    title=f"Projeto {index}",
                    quantity=1,
                ),
            )
        requirement = self.scoring.calculate_requirement(
            self.process, requirement_id(2)
        )
        self.assertEqual(requirement.total_score, Decimal("15"))
        self.assertEqual(len(requirement.activity_scores), 2)

    def test_validation_distinguishes_draft_warning_and_complete_error(self):
        draft = self.activities.create_activity(
            criterion_id=criterion_id(1, 1),
            title="Rascunho",
            quantity=1,
        )
        complete = self.activities.create_activity(
            criterion_id=criterion_id(1, 2),
            title="Completa",
            quantity=1,
            status=ActivityStatus.COMPLETE,
        )

        draft_result = self.validation.validate_activity(draft)
        complete_result = self.validation.validate_activity(complete)

        self.assertTrue(draft_result.is_valid)
        self.assertEqual(draft_result.warning_count, 1)
        self.assertFalse(complete_result.is_valid)
        self.assertEqual(complete_result.error_count, 1)

    def test_validation_reports_process_fields_and_invalid_references(self):
        invalid_process = RscProcess("", "")
        invalid_activity = RscActivity(
            criterion_id="rsc.criterion.99.1",
            title="Critério ausente",
            quantity=1,
            evidence_ids=("evidence-missing",),
        )
        invalid_process.add_activity(invalid_activity)

        result = self.validation.validate_process(invalid_process)
        codes = {issue.code for issue in result.issues}

        self.assertIn("process.applicant_name.missing", codes)
        self.assertIn("process.institution.missing", codes)
        self.assertIn("activity.criterion.invalid", codes)
        self.assertIn("activity.evidence.reference_missing", codes)
        self.assertEqual(result.warning_count, 0)
        self.assertGreaterEqual(result.error_count, 4)
        self.assertFalse(result.is_valid)

    def test_empty_process_is_valid_and_variant_errors_are_structured(self):
        self.assertTrue(self.validation.validate_process(self.process).is_valid)
        missing_variant = RscActivity(
            criterion_id=criterion_id(5, 1),
            title="Direção",
            quantity=1,
        )
        forbidden_variant = RscActivity(
            criterion_id=criterion_id(1, 1),
            title="Conselho",
            quantity=1,
            score_variant_id="indevida",
        )

        self.assertIn(
            "activity.variant.required",
            {
                issue.code
                for issue in self.validation.validate_activity(
                    missing_variant
                ).issues
            },
        )
        self.assertIn(
            "activity.variant.forbidden",
            {
                issue.code
                for issue in self.validation.validate_activity(
                    forbidden_variant
                ).issues
            },
        )


class RscSessionIntegrationTests(unittest.TestCase):
    class EvidenceLookup:
        def exists(self, _evidence_id):
            return True

    def test_session_exposes_and_disposes_foundation_services(self):
        application = RscApplication()
        session = application.create_project_session(self.EvidenceLookup())

        self.assertEqual(session.official_catalog.count_criteria(), 55)
        process = session.rsc_process_service.create_process(
            applicant_name="Pessoa",
            institution="Instituição",
        )
        activity = session.rsc_activity_service.create_activity(
            criterion_id=criterion_id(1, 1),
            title="Conselho",
            quantity=1,
        )
        session.rsc_activity_service.add_activity(process, activity)
        application.dispose()

        self.assertEqual(session.rsc_process_service.count_processes(), 0)
        self.assertEqual(session.rsc_evidence_service._evidence, {})


if __name__ == "__main__":
    unittest.main()
