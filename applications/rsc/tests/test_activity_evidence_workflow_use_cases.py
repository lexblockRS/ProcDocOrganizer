import unittest
from uuid import uuid4

from applications.rsc import RscApplication
from applications.rsc.domain import criterion_id, requirement_id
from applications.rsc.use_cases import (
    ActivityNotFoundError,
    CreateActivityCommand,
    CreateActivityUseCase,
    CreateEvidenceCommand,
    CreateEvidenceUseCase,
    CreateProcessCommand,
    CreateProcessUseCase,
    DocumentNotFoundError,
    DomainValidationError,
    EvidenceNotFoundError,
    GetActivityCommand,
    GetActivityUseCase,
    GetEvidenceCommand,
    GetEvidenceUseCase,
    ListActivitiesByCriterionCommand,
    ListActivitiesByCriterionUseCase,
    ListActivitiesByRequirementCommand,
    ListActivitiesByRequirementUseCase,
    ListActivitiesCommand,
    ListActivitiesUseCase,
    ListEvidenceByActivityCommand,
    ListEvidenceByActivityUseCase,
    ListEvidenceCommand,
    ListEvidenceUseCase,
    RegisterDocumentCommand,
    RegisterDocumentUseCase,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class ActivityEvidenceWorkflowUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.session = RscApplication().create_project_session(
            EvidenceLookup()
        )
        self.registry = self.session.use_cases
        self.process = self.registry.get(CreateProcessUseCase).execute(
            CreateProcessCommand("Pessoa", "Instituição")
        )

    def create_activity(self, criterion=criterion_id(1, 1), **values):
        return self.registry.get(CreateActivityUseCase).execute(
            CreateActivityCommand(
                process_id=self.process.process_id,
                criterion_id=criterion,
                title=values.pop("title", "Atividade"),
                quantity=values.pop("quantity", "1"),
                **values,
            )
        )

    def register_document(self, name="ato.pdf"):
        return self.registry.get(RegisterDocumentUseCase).execute(
            RegisterDocumentCommand(self.process.process_id, name)
        )

    def test_create_activity_and_query_all_views(self):
        first = self.create_activity(criterion_id(1, 1), title="Conselho")
        second = self.create_activity(criterion_id(1, 2), title="Comissão")
        third = self.create_activity(criterion_id(2, 1), title="Projeto")

        fetched = self.registry.get(GetActivityUseCase).execute(
            GetActivityCommand(self.process.process_id, first.activity_id)
        )
        all_items = self.registry.get(ListActivitiesUseCase).execute(
            ListActivitiesCommand(self.process.process_id)
        )
        by_criterion = self.registry.get(
            ListActivitiesByCriterionUseCase
        ).execute(
            ListActivitiesByCriterionCommand(
                self.process.process_id, criterion_id(1, 2)
            )
        )
        by_requirement = self.registry.get(
            ListActivitiesByRequirementUseCase
        ).execute(
            ListActivitiesByRequirementCommand(
                self.process.process_id, requirement_id(1)
            )
        )

        self.assertEqual(fetched.activity, first.activity)
        self.assertEqual(
            all_items.activities,
            (first.activity, second.activity, third.activity),
        )
        self.assertEqual(by_criterion.activities, (second.activity,))
        self.assertEqual(
            by_requirement.activities, (first.activity, second.activity)
        )

    def test_activity_rejects_unknown_criterion_and_invalid_quantity(self):
        with self.assertRaises(DomainValidationError):
            self.create_activity("rsc.criterion.9.1")
        with self.assertRaises(DomainValidationError):
            self.create_activity(quantity="0")
        with self.assertRaises(ActivityNotFoundError):
            self.registry.get(GetActivityUseCase).execute(
                GetActivityCommand(
                    self.process.process_id, str(uuid4())
                )
            )

    def test_activity_enforces_required_and_forbidden_variants(self):
        variant_criterion = criterion_id(5, 1)
        with self.assertRaises(DomainValidationError):
            self.create_activity(variant_criterion)
        titular = self.create_activity(
            variant_criterion,
            score_variant_id=f"{variant_criterion}.titular",
        )
        self.assertEqual(
            titular.activity.score_variant_id,
            f"{variant_criterion}.titular",
        )
        with self.assertRaises(DomainValidationError):
            self.create_activity(
                criterion_id(1, 1), score_variant_id="indevida"
            )

    def test_create_evidence_links_it_automatically_to_activity(self):
        activity = self.create_activity()
        first_document = self.register_document("ato.pdf")
        second_document = self.register_document("portaria.pdf")

        result = self.registry.get(CreateEvidenceUseCase).execute(
            CreateEvidenceCommand(
                process_id=self.process.process_id,
                activity_id=activity.activity_id,
                document_ids=(
                    first_document.document_id,
                    second_document.document_id,
                ),
                description="Atos comprobatórios",
            )
        )
        updated_activity = self.registry.get(GetActivityUseCase).execute(
            GetActivityCommand(
                self.process.process_id, activity.activity_id
            )
        ).activity

        self.assertEqual(
            result.evidence.document_ids,
            (first_document.document_id, second_document.document_id),
        )
        self.assertEqual(updated_activity.evidence_ids, (result.evidence_id,))

    def test_evidence_queries_return_global_and_activity_scopes(self):
        activity = self.create_activity()
        document = self.register_document()
        created = self.registry.get(CreateEvidenceUseCase).execute(
            CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (document.document_id,),
                "Ato",
            )
        )

        fetched = self.registry.get(GetEvidenceUseCase).execute(
            GetEvidenceCommand(created.evidence_id)
        )
        all_items = self.registry.get(ListEvidenceUseCase).execute(
            ListEvidenceCommand()
        )
        by_activity = self.registry.get(
            ListEvidenceByActivityUseCase
        ).execute(
            ListEvidenceByActivityCommand(
                self.process.process_id, activity.activity_id
            )
        )

        self.assertEqual(fetched.evidence, created.evidence)
        self.assertEqual(all_items.evidence, (created.evidence,))
        self.assertEqual(by_activity.evidence, (created.evidence,))

    def test_evidence_rejects_missing_duplicate_and_unrelated_documents(self):
        activity = self.create_activity()
        document = self.register_document()
        create = self.registry.get(CreateEvidenceUseCase)

        with self.assertRaises(DocumentNotFoundError):
            create.execute(CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (str(uuid4()),),
                "Ausente",
            ))
        with self.assertRaises(DomainValidationError):
            create.execute(CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (document.document_id, document.document_id),
                "Duplicada",
            ))

        other_process = self.registry.get(CreateProcessUseCase).execute(
            CreateProcessCommand("Outra", "Instituição")
        )
        other_document = self.registry.get(RegisterDocumentUseCase).execute(
            RegisterDocumentCommand(other_process.process_id, "outro.pdf")
        )
        with self.assertRaises(DocumentNotFoundError):
            create.execute(CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (other_document.document_id,),
                "Outro processo",
            ))

    def test_evidence_rejects_missing_activity_and_reports_missing_evidence(self):
        document = self.register_document()
        with self.assertRaises(ActivityNotFoundError):
            self.registry.get(CreateEvidenceUseCase).execute(
                CreateEvidenceCommand(
                    self.process.process_id,
                    str(uuid4()),
                    (document.document_id,),
                    "Atividade ausente",
                )
            )
        with self.assertRaises(EvidenceNotFoundError):
            self.registry.get(GetEvidenceUseCase).execute(
                GetEvidenceCommand(str(uuid4()))
            )

    def test_dispose_clears_activity_evidence_session_state(self):
        activity = self.create_activity()
        document = self.register_document()
        self.registry.get(CreateEvidenceUseCase).execute(
            CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (document.document_id,),
                "Ato",
            )
        )

        self.session.dispose()

        self.assertEqual(self.session.rsc_process_service.count_processes(), 0)
        self.assertEqual(self.session.rsc_evidence_service.list_all(), ())
        self.assertEqual(self.session.rsc_document_service.list_documents(), ())


if __name__ == "__main__":
    unittest.main()
