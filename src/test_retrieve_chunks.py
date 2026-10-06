"""Chroma integration tests for same-model top-k retrieval."""

import tempfile
import unittest
from pathlib import Path

from src.embedding_demo import OFFLINE_QUERY_VECTOR, OFFLINE_VECTORS, SAMPLE_CHUNKS
from src.retrieve_chunks import (
    render_retrieval_report,
    retrieve_top_k,
    validate_query_vector,
)
from src.vector_store import connect_vector_store, get_dimension_checked_collection


class RetrieveChunksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.client, _ = connect_vector_store(Path(self.temporary_directory.name) / "chroma")
        self.collection = get_dimension_checked_collection(
            self.client, "retrieval-test", "offline-fixture-v2", 8
        )
        self.collection.upsert(
            ids=["policy", "faq", "onboarding", "probe"],
            embeddings=[*[list(vector) for vector in OFFLINE_VECTORS], list(OFFLINE_QUERY_VECTOR)],
            documents=[chunk["text"] for chunk in SAMPLE_CHUNKS] + ["readback probe"],
            metadatas=[
                {**chunk["metadata"], "record_type": "corpus_chunk"}
                for chunk in SAMPLE_CHUNKS
            ]
            + [{"record_type": "readback_test", "source": "probe.txt"}],
        )

    def tearDown(self) -> None:
        self.client.close()
        self.temporary_directory.cleanup()

    def test_query_model_and_dimension_must_match_collection(self) -> None:
        self.assertEqual(validate_query_vector(self.collection, "offline-fixture-v2", OFFLINE_QUERY_VECTOR), 8)
        with self.assertRaisesRegex(ValueError, "model"):
            validate_query_vector(self.collection, "wrong-model", OFFLINE_QUERY_VECTOR)
        with self.assertRaisesRegex(ValueError, "dimension"):
            validate_query_vector(self.collection, "offline-fixture-v2", [0.1, 0.2])

    def test_top_k_results_are_ordered_and_exclude_non_corpus_records(self) -> None:
        top_one = retrieve_top_k(self.collection, OFFLINE_QUERY_VECTOR, 1)
        top_three = retrieve_top_k(self.collection, OFFLINE_QUERY_VECTOR, 3)

        self.assertEqual(len(top_one), 1)
        self.assertEqual(len(top_three), 3)
        self.assertEqual(
            [item["metadata"]["source"] for item in top_three],
            ["policy.txt", "faq.html", "onboarding.md"],
        )
        self.assertGreater(top_three[0]["score"], top_three[1]["score"])
        self.assertGreater(top_three[1]["score"], top_three[2]["score"])
        self.assertEqual(top_three[0]["text"], SAMPLE_CHUNKS[0]["text"])
        self.assertEqual(top_three[0]["metadata"]["chunk_index"], 1)
        self.assertNotIn("probe.txt", [item["metadata"].get("source") for item in top_three])

    def test_report_demonstrates_k_values_and_metadata(self) -> None:
        results = {
            1: retrieve_top_k(self.collection, OFFLINE_QUERY_VECTOR, 1),
            3: retrieve_top_k(self.collection, OFFLINE_QUERY_VECTOR, 3),
        }

        report = render_retrieval_report(
            query="Can I get a refund for an annual plan within 30 days?",
            model="offline-fixture-v2",
            dimension=8,
            k_values=(1, 3),
            results_by_k=results,
        )

        self.assertIn("k = 1", report)
        self.assertIn("k = 3", report)
        self.assertIn("0.999438", report)
        self.assertIn("policy.txt", report)
        self.assertIn("chunk_index", report)


if __name__ == "__main__":
    unittest.main()