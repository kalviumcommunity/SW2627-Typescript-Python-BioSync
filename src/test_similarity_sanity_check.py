"""Offline tests for the retrieval similarity sanity evaluator."""

import unittest

from src.similarity_sanity_check import (
    SANITY_CASES,
    SanityCase,
    evaluate_cases,
    render_report,
)


class SimilaritySanityCheckTests(unittest.TestCase):
    def test_known_related_sources_rank_above_unrelated_sources(self) -> None:
        report = evaluate_cases()

        self.assertEqual(report["test_count"], 3)
        self.assertEqual(report["passes"], 3)
        self.assertEqual(report["failures"], 0)
        for result in report["results"]:
            self.assertTrue(result["relevant_above_unrelated"], result["case_id"])

    def test_close_refund_source_order_is_reported_as_surprising(self) -> None:
        report = evaluate_cases()
        surprise = next(result for result in report["results"] if result["surprising"])

        self.assertEqual(surprise["top_source"], "policy.txt")
        self.assertEqual(surprise["preferred_source"], "faq.html")
        self.assertLess(surprise["top_margin_over_preferred"], 0.001)
        self.assertEqual(report["surprising_cases"], 1)

    def test_missing_relevant_source_is_counted_as_failure(self) -> None:
        impossible_case = SanityCase(
            case_id="unknown-source",
            query="A query with a missing relevant label",
            query_vector=SANITY_CASES[0].query_vector,
            relevant_sources=("missing.txt",),
        )

        report = evaluate_cases((impossible_case,))

        self.assertEqual(report["passes"], 0)
        self.assertEqual(report["failures"], 1)
        self.assertFalse(report["results"][0]["relevant_above_unrelated"])

    def test_rendered_report_explains_fixture_limit_and_quality_metrics(self) -> None:
        rendered = render_report(evaluate_cases())

        self.assertIn("Test cases: 3", rendered)
        self.assertIn("Surprising / borderline cases: 1", rendered)
        self.assertIn("0.000124", rendered)
        self.assertIn("Recall@k, MRR, or nDCG", rendered)
        self.assertIn("Mismatched embedding models", rendered)


if __name__ == "__main__":
    unittest.main()