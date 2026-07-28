from datetime import timezone
import unittest
from uuid import UUID, uuid4

from applications.rsc import RscApplication
from applications.rsc.domain import RscProcessStatus
from applications.rsc.use_cases import (
    CreateProcessCommand,
    CreateProcessUseCase,
    DocumentNotFoundError,
    DuplicateEntityError,
    GetDocumentCommand,
    GetDocumentUseCase,
    GetProcessCommand,
    GetProcessUseCase,
    InvalidCommandError,
    ListDocumentsCommand,
    ListDocumentsUseCase,
    ListProcessesCommand,
    ListProcessesUseCase,
    ProcessNotFoundError,
    RegisterDocumentCommand,
    RegisterDocumentUseCase,
    RemoveDocumentCommand,
    RemoveDocumentUseCase,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class ProcessLifecycleUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.session = RscApplication().create_project_session(
            EvidenceLookup()
        )
        self.registry = self.session.use_cases

    def create_process(self):
        return self.registry.get(CreateProcessUseCase).execute(
            CreateProcessCommand("Pessoa", "Instituição", "123")
        )

    def test_create_process_returns_uuid_timestamps_and_draft(self):
        result = self.create_process()

        UUID(result.process_id)
        self.assertIsNotNone(result.created_at.astimezone(timezone.utc))
        self.assertEqual(result.process.status, RscProcessStatus.DRAFT)
        self.assertEqual(
            self.registry.get(GetProcessUseCase).execute(
                GetProcessCommand(result.process_id)
            ).process,
            result.process,
        )

    def test_create_process_validates_command_and_required_fields(self):
        use_case = self.registry.get(CreateProcessUseCase)

        with self.assertRaises(InvalidCommandError):
            use_case.execute(None)
        with self.assertRaises(InvalidCommandError):
            use_case.execute(CreateProcessCommand("", "Instituição"))
        with self.assertRaises(ProcessNotFoundError):
            self.registry.get(GetProcessUseCase).execute(
                GetProcessCommand(str(uuid4()))
            )
        with self.assertRaises(InvalidCommandError):
            self.registry.get(GetProcessUseCase).execute(
                GetProcessCommand("não-é-uuid")
            )

    def test_register_and_query_document_without_opening_path(self):
        process = self.create_process()
        command = RegisterDocumentCommand(
            process_id=process.process_id,
            file_name="ato.pdf",
            original_path="Z:/caminho/inexistente/ato.pdf",
            mime_type="application/pdf",
        )

        registered = self.registry.get(RegisterDocumentUseCase).execute(
            command
        )
        document = self.registry.get(GetDocumentUseCase).execute(
            GetDocumentCommand(registered.document_id)
        ).document
        listed = self.registry.get(ListDocumentsUseCase).execute(
            ListDocumentsCommand(process.process_id)
        )

        UUID(registered.document_id)
        self.assertEqual(document.file_name, "ato.pdf")
        self.assertEqual(
            document.original_path, "Z:/caminho/inexistente/ato.pdf"
        )
        self.assertEqual(listed.documents, (document,))
        self.assertIn(registered.document_id, process.process.document_ids)

    def test_duplicate_document_identity_is_rejected_consistently(self):
        process = self.create_process()
        document_id = str(uuid4())
        command = RegisterDocumentCommand(
            process.process_id, "ato.pdf", document_id=document_id
        )
        register = self.registry.get(RegisterDocumentUseCase)
        register.execute(command)

        with self.assertRaises(DuplicateEntityError):
            register.execute(command)
        self.assertEqual(
            process.process.document_ids, (document_id,)
        )
        self.assertEqual(
            len(self.session.rsc_document_service.list_documents()), 1
        )

    def test_queries_list_processes_and_report_missing_documents(self):
        first = self.create_process()
        second = self.create_process()

        processes = self.registry.get(ListProcessesUseCase).execute(
            ListProcessesCommand()
        )

        self.assertEqual(
            tuple(item.id for item in processes.processes),
            (first.process_id, second.process_id),
        )
        with self.assertRaises(DocumentNotFoundError):
            self.registry.get(GetDocumentUseCase).execute(
                GetDocumentCommand(str(uuid4()))
            )

    def test_remove_document_updates_process_and_storage(self):
        process = self.create_process()
        registered = self.registry.get(RegisterDocumentUseCase).execute(
            RegisterDocumentCommand(process.process_id, "ato.pdf")
        )

        removed = self.registry.get(RemoveDocumentUseCase).execute(
            RemoveDocumentCommand(
                process.process_id, registered.document_id
            )
        )

        self.assertEqual(removed.document_id, registered.document_id)
        self.assertEqual(process.process.document_ids, ())
        self.assertEqual(
            self.session.rsc_document_service.list_documents(), ()
        )
        with self.assertRaises(DocumentNotFoundError):
            self.registry.get(RemoveDocumentUseCase).execute(
                RemoveDocumentCommand(
                    process.process_id, registered.document_id
                )
            )

    def test_document_operations_require_existing_process(self):
        missing = str(uuid4())
        with self.assertRaises(ProcessNotFoundError):
            self.registry.get(RegisterDocumentUseCase).execute(
                RegisterDocumentCommand(missing, "ato.pdf")
            )
        with self.assertRaises(ProcessNotFoundError):
            self.registry.get(ListDocumentsUseCase).execute(
                ListDocumentsCommand(missing)
            )


if __name__ == "__main__":
    unittest.main()
