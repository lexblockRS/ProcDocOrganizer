from dataclasses import FrozenInstanceError
from fractions import Fraction
import unittest

from presentation import (
    CoverageContractError,
    CoverageFinding,
    CoverageInput,
    CoverageScope,
    CoverageState,
    DocumentCoverageReference,
    EvidenceCoverageReference,
    ExecutionFactCoverageReference,
    OverallCoverage,
    ResourceIdentity,
    ResourceType,
)


def identity(resource_type, identifier):
    return ResourceIdentity(resource_type, identifier)


class CoverageContractTests(unittest.TestCase):
    def test_input_is_immutable_and_contains_only_normalized_references(self):
        document = identity(ResourceType.DOCUMENT, "doc-1")
        evidence = identity(ResourceType.EVIDENCE, "ev-1")
        fact = identity(ResourceType.EXECUTION_FACT, "fact-1")
        coverage_input = CoverageInput(
            " project-1 ",
            2,
            (DocumentCoverageReference(document, (evidence,)),),
            (EvidenceCoverageReference(evidence, (document,), (fact,)),),
            (ExecutionFactCoverageReference(fact, evidence),),
        )

        self.assertEqual(coverage_input.project_id, "project-1")
        with self.assertRaises(FrozenInstanceError):
            coverage_input.project_revision = 3

    def test_references_reject_wrong_types_and_duplicates(self):
        document = identity(ResourceType.DOCUMENT, "doc-1")
        evidence = identity(ResourceType.EVIDENCE, "ev-1")
        with self.assertRaises(CoverageContractError):
            DocumentCoverageReference(evidence)
        with self.assertRaises(CoverageContractError):
            EvidenceCoverageReference(
                evidence, (document, document)
            )

    def test_finding_is_explainable_and_references_only_identities(self):
        document = identity(ResourceType.DOCUMENT, "doc-1")
        finding = CoverageFinding(
            CoverageScope.DOCUMENT,
            document,
            CoverageState.ABSENT,
            0,
            1,
            "O Document não possui relação com Evidence.",
            ("DOCUMENT_WITHOUT_EVIDENCE",),
        )

        self.assertTrue(finding.explanation)
        self.assertTrue(finding.reason_codes)
        with self.assertRaises(FrozenInstanceError):
            finding.state = CoverageState.COMPLETE
        with self.assertRaises(CoverageContractError):
            CoverageFinding(
                CoverageScope.DOCUMENT,
                document,
                CoverageState.ABSENT,
                0,
                1,
                "Explicação",
                (),
            )

    def test_overall_ratio_must_be_exact(self):
        coverage = OverallCoverage(
            CoverageState.PARTIAL, 2, 3, Fraction(2, 3)
        )
        self.assertEqual(coverage.ratio, Fraction(2, 3))
        with self.assertRaises(CoverageContractError):
            OverallCoverage(
                CoverageState.PARTIAL, 2, 3, Fraction(1, 2)
            )


if __name__ == "__main__":
    unittest.main()
