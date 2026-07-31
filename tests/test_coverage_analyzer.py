import ast
from pathlib import Path
import unittest

from presentation import (
    BindingCoverageReference,
    CoverageAnalyzer,
    CoverageInput,
    CoverageState,
    DocumentCoverageReference,
    EvaluationCoverageSnapshot,
    EvidenceCoverageReference,
    ExecutionFactCoverageReference,
    NormativeCoverageReference,
    ResourceIdentity,
    ResourceType,
)


def identity(resource_type, identifier):
    return ResourceIdentity(resource_type, identifier)


class CoverageAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.d1 = identity(ResourceType.DOCUMENT, "doc-1")
        self.d2 = identity(ResourceType.DOCUMENT, "doc-2")
        self.d3 = identity(ResourceType.DOCUMENT, "doc-3")
        self.e1 = identity(ResourceType.EVIDENCE, "ev-1")
        self.e2 = identity(ResourceType.EVIDENCE, "ev-2")
        self.e3 = identity(ResourceType.EVIDENCE, "ev-3")
        self.f1 = identity(ResourceType.EXECUTION_FACT, "fact-1")
        self.f2 = identity(ResourceType.EXECUTION_FACT, "fact-2")
        self.requirement = identity(ResourceType.REQUIREMENT, "req-1")
        self.criterion1 = identity(ResourceType.CRITERION, "criterion-1")
        self.criterion2 = identity(ResourceType.CRITERION, "criterion-2")

    def input(self, *, evaluation=True):
        snapshot = None
        if evaluation:
            snapshot = EvaluationCoverageSnapshot(
                "evaluation-1",
                4,
                used_evidences=(self.e1,),
                used_execution_facts=(self.f1,),
                validated_execution_facts=(self.f1, self.f2),
                compatible_execution_facts=(self.f1,),
                normative_results=(
                    NormativeCoverageReference(
                        self.requirement, "PARTIAL"
                    ),
                    NormativeCoverageReference(
                        self.criterion1, "EXECUTED"
                    ),
                    NormativeCoverageReference(
                        self.criterion2, "NOT_EXECUTED"
                    ),
                ),
            )
        return CoverageInput(
            "project-1",
            8,
            documents=(
                DocumentCoverageReference(self.d1, (self.e1,)),
                DocumentCoverageReference(self.d2),
                DocumentCoverageReference(self.d3, (self.e1, self.e2)),
            ),
            evidences=(
                EvidenceCoverageReference(
                    self.e1, (self.d1, self.d3), (self.f1,)
                ),
                EvidenceCoverageReference(
                    self.e2, (self.d3,), (self.f2,)
                ),
                EvidenceCoverageReference(self.e3),
            ),
            execution_facts=(
                ExecutionFactCoverageReference(self.f1, self.e1),
                ExecutionFactCoverageReference(self.f2, self.e2),
            ),
            bindings=(BindingCoverageReference("binding-1", self.f1),),
            evaluation=snapshot,
        )

    def test_calculates_all_dimensions_without_averages(self):
        result = CoverageAnalyzer().analyze(self.input())

        self.assertEqual(
            (
                result.document_coverage.total,
                result.document_coverage.used,
                result.document_coverage.unused,
                result.document_coverage.multiple_evidences,
            ),
            (3, 2, 1, 1),
        )
        self.assertEqual(result.evidence_coverage.with_documents, 2)
        self.assertEqual(result.evidence_coverage.with_execution_facts, 2)
        self.assertEqual(result.evidence_coverage.evaluated, 1)
        self.assertEqual(result.factual_coverage.bound, 1)
        self.assertEqual(result.factual_coverage.unbound, 1)
        self.assertEqual(result.factual_coverage.evaluated, 1)
        self.assertEqual(result.factual_coverage.validated, 2)
        self.assertEqual(result.factual_coverage.compatible, 1)
        self.assertEqual(result.overall_coverage.covered, 7)
        self.assertEqual(result.overall_coverage.total, 11)
        self.assertIs(result.overall_coverage.state, CoverageState.PARTIAL)

    def test_normative_coverage_only_projects_existing_states(self):
        result = CoverageAnalyzer().analyze(self.input())

        self.assertIs(
            result.normative_coverage.state, CoverageState.COMPLETE
        )
        self.assertEqual(result.normative_coverage.requirements_total, 1)
        self.assertEqual(result.normative_coverage.criteria_total, 2)
        self.assertEqual(
            tuple(
                (item.state, item.count)
                for item in result.normative_coverage.criterion_states
            ),
            (("EXECUTED", 1), ("NOT_EXECUTED", 1)),
        )

        without_evaluation = CoverageAnalyzer().analyze(
            self.input(evaluation=False)
        )
        self.assertIs(
            without_evaluation.normative_coverage.state,
            CoverageState.NOT_EVALUATED,
        )

    def test_findings_are_explainable_and_multidimensional(self):
        result = CoverageAnalyzer().analyze(self.input())
        reasons = {
            code
            for finding in result.findings
            for code in finding.reason_codes
        }
        self.assertIn("DOCUMENT_WITHOUT_EVIDENCE", reasons)
        self.assertIn("EVIDENCE_WITHOUT_DOCUMENT", reasons)
        self.assertIn("EVIDENCE_WITHOUT_EXECUTION_FACT", reasons)
        self.assertIn("EXECUTION_FACT_WITHOUT_BINDING", reasons)
        self.assertTrue(all(item.explanation for item in result.findings))
        self.assertEqual(result.factual_coverage.total, 2)
        self.assertEqual(result.factual_coverage.pending, 1)

    def test_is_deterministic_and_preserves_source_revisions(self):
        analyzer = CoverageAnalyzer()
        coverage_input = self.input()

        first = analyzer.analyze(coverage_input)
        second = analyzer.analyze(coverage_input)

        self.assertEqual(first, second)
        self.assertEqual(first.source_revisions.project_revision, 8)
        self.assertEqual(first.source_revisions.evaluation_revision, 4)
        self.assertEqual(first.analysis_version, "1.0")
        self.assertIsNone(first.generated_at)

    def test_detects_structural_inconsistency_without_interpreting_it(self):
        missing_document = identity(ResourceType.DOCUMENT, "missing")
        coverage_input = CoverageInput(
            "project-1",
            1,
            evidences=(EvidenceCoverageReference(
                self.e1, (missing_document,), ()
            ),),
        )

        result = CoverageAnalyzer().analyze(coverage_input)

        self.assertIs(
            result.evidence_coverage.state, CoverageState.INCONSISTENT
        )
        self.assertIn(
            "EVIDENCE_DANGLING_REFERENCE",
            result.findings[0].reason_codes,
        )


class CoverageArchitectureTests(unittest.TestCase):
    def test_coverage_modules_are_independent_of_forbidden_layers(self):
        forbidden = (
            "pyside", "pyqt", "database", "sqlite", "stores", "domain",
            "kernel", "validation", "compatibility", "pipeline",
            "main_window", "views", "insights",
        )
        for path in (
            Path("presentation/coverage.py"),
            Path("presentation/coverage_analyzer.py"),
        ):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            modules = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            } | {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            for module in modules:
                self.assertFalse(
                    any(item in module.casefold() for item in forbidden),
                    (path, module),
                )


if __name__ == "__main__":
    unittest.main()
