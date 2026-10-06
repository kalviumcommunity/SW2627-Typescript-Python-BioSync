"""Integration tests for corpus embedding indexing into Chroma."""

import tempfile
import unittest
from pathlib import Path

from src.index_corpus import index_embedded_chunks, render_index_report
from src.vector_store import connect_vector_store


class CorpusIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "chroma"
        self.client, self.heartbeat = connect_vector_store(self.db_path)

    def tearDown(self) -> None:
        self.client.close()
        self.temporary_directory.cleanup()

    @staticmethod
    def sample_rows() -> tuple[list[dict], list[dict]]:
        chunks = [
            {
                "text": "Refunds are available within 30 days.",
                "metadata": {
                    "source": "policy.txt",
                    "section": "refunds",
                    "chunk_index": 1,
                    "position_start": 0,
                    "position_end": 37,
                    "page": None,
                },
            },
            {
                "text": "Use the account email to find a record.",
                "metadata": {
                    "source": "onboarding.md",
                    "section": "accounts",
                    "chunk_index": 1,
                    "position_start": 0,
                    "position_end": 39,
                    "page": None,
                },
            },
        ]
        embedded = [
            {**chunk, "embedding": [float(index + 1), 0.5, 0.25]}
            for index, chunk in enumerate(chunks)
        ]
        return chunks, embedded

    def test_index_count_and_spot_check_match_source_record(self) -> None:
        chunks, embedded = self.sample_rows()

        summary = index_embedded_chunks(
            chunks,
            embedded,
            self.client,
            "test-model",
            "corpus-test",
            prior_ingestion_count=2,
        )

        self.assertEqual(summary["expected_chunks"], 2)
        self.assertEqual(summary["indexed_count"], 2)
        self.assertTrue(summary["count_matches"])
        self.assertTrue(summary["prior_count_matches"])
        self.assertTrue(summary["spot_check_matches"])
        self.assertEqual(summary["spot_check"]["text"], chunks[0]["text"])
        self.assertEqual(summary["spot_check"]["metadata"]["source"], "policy.txt")
        self.assertEqual(summary["spot_check"]["vector_length"], 3)
        self.assertNotIn("page", summary["spot_check"]["metadata"])

    def test_rerun_is_idempotent_and_removes_stale_corpus_rows(self) -> None:
        chunks, embedded = self.sample_rows()
        first = index_embedded_chunks(
            chunks, embedded, self.client, "test-model", "corpus-test"
        )

        second = index_embedded_chunks(
            chunks[:1],
            embedded[:1],
            self.client,
            "test-model",
            "corpus-test",
            prior_ingestion_count=1,
        )

        self.assertEqual(first["indexed_count"], 2)
        self.assertEqual(second["indexed_count"], 1)
        self.assertEqual(second["stale_records_removed"], 1)
        self.assertTrue(second["count_matches"])

    def test_prior_ingestion_count_mismatch_is_reported(self) -> None:
        chunks, embedded = self.sample_rows()

        summary = index_embedded_chunks(
            chunks,
            embedded,
            self.client,
            "test-model",
            "corpus-test",
            prior_ingestion_count=99,
        )

        self.assertFalse(summary["prior_count_matches"])
        self.assertTrue(any("prior ingestion summary records 99" in item for item in summary["failures"]))

    def test_report_contains_count_and_readback_evidence(self) -> None:
        chunks, embedded = self.sample_rows()
        summary = index_embedded_chunks(
            chunks, embedded, self.client, "test-model", "corpus-test"
        )
        rendered = render_index_report(
            summary,
            db_path=self.db_path,
            heartbeat=self.heartbeat,
            embedding_summary=type("EmbeddingSummary", (), {"skipped_chunks": 0, "failed_chunks": 0})(),
        )

        self.assertIn("Indexed corpus records: 2", rendered)
        self.assertIn("Count matches: yes", rendered)
        self.assertIn("Matches source chunk: yes", rendered)
        self.assertIn("Vector length: 3", rendered)


if __name__ == "__main__":
    unittest.main()