"""Offline checks for embedding generation and similarity reporting."""

import unittest
from types import SimpleNamespace

from src.embedding_demo import (
    OFFLINE_VECTORS,
    OFFLINE_QUERY_VECTOR,
    SAMPLE_QUERY,
    SAMPLE_TEXTS,
    cosine_similarity,
    embed_chunks,
    generate_embeddings,
    rank_chunks,
    render_report,
    render_similarity_report,
    render_storage_report,
    SAMPLE_CHUNKS,
    stored_embeddings_from_vectors,
)


class EmbeddingDemoTests(unittest.TestCase):
    def test_provider_vectors_are_ordered_and_have_one_dimension(self) -> None:
        response = SimpleNamespace(
            data=[
                SimpleNamespace(index=1, embedding=[2.0, 0.0]),
                SimpleNamespace(index=0, embedding=[1.0, 0.0]),
            ]
        )
        client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **_: response))

        vectors = generate_embeddings(("first", "second"), client, "test-model")

        self.assertEqual(vectors, [[1.0, 0.0], [2.0, 0.0]])

    def test_similar_pair_scores_higher_than_dissimilar_pair(self) -> None:
        similar = cosine_similarity(OFFLINE_VECTORS[0], OFFLINE_VECTORS[1])
        dissimilar = cosine_similarity(OFFLINE_VECTORS[0], OFFLINE_VECTORS[2])

        self.assertGreater(similar, dissimilar)

    def test_report_confirms_dimension_and_comparison(self) -> None:
        report = render_report(SAMPLE_TEXTS, OFFLINE_VECTORS, "test fixture")

        self.assertIn("Vector dimension: 8", report)
        self.assertIn("All vectors same length: True", report)
        self.assertIn("Similar pair scores higher: True", report)
        self.assertIn("numeric representation", report)

    def test_api_embeddings_are_stored_with_text_and_metadata(self) -> None:
        response = SimpleNamespace(
            data=[
                SimpleNamespace(index=1, embedding=[0.2, 0.3]),
                SimpleNamespace(index=0, embedding=[0.1, 0.4]),
                SimpleNamespace(index=2, embedding=[0.5, 0.6]),
            ]
        )
        client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **_: response))

        records = embed_chunks(SAMPLE_CHUNKS, client, "test-model")

        self.assertEqual(records[0].text, SAMPLE_CHUNKS[0]["text"])
        self.assertEqual(records[0].metadata["source"], "policy.txt")
        self.assertEqual(records[1].vector, [0.2, 0.3])

    def test_storage_report_confirms_chunk_count_and_vector_samples(self) -> None:
        records = stored_embeddings_from_vectors(SAMPLE_CHUNKS, OFFLINE_VECTORS)

        report = render_storage_report(records, "test fixture")

        self.assertIn("Chunks embedded: 3", report)
        self.assertIn("Vector length: 8", report)
        self.assertIn("Metadata: `{'source': 'policy.txt'", report)
        self.assertIn("Vector sample: [0.9100, 0.1200", report)

    def test_query_ranks_refund_chunks_above_unrelated_chunk(self) -> None:
        records = stored_embeddings_from_vectors(SAMPLE_CHUNKS, OFFLINE_VECTORS)

        ranked = rank_chunks(OFFLINE_QUERY_VECTOR, records)

        self.assertEqual([record.metadata["source"] for _, record in ranked], [
            "policy.txt",
            "faq.html",
            "onboarding.md",
        ])
        self.assertGreater(ranked[0][0], ranked[-1][0])

    def test_similarity_report_shows_query_metric_and_ranked_sources(self) -> None:
        records = stored_embeddings_from_vectors(SAMPLE_CHUNKS, OFFLINE_VECTORS)

        report = render_similarity_report(SAMPLE_QUERY, OFFLINE_QUERY_VECTOR, records, "test fixture")

        self.assertIn("Cosine similarity compares vector direction", report)
        self.assertIn("## Most similar", report)
        self.assertIn("## Least similar", report)
        self.assertIn("annual plan refunds are available within thirty days", report)
        self.assertIn("the office cafeteria serves soup on Thursdays", report)
        self.assertIn("'source': 'policy.txt'", report)
        self.assertIn("'source': 'onboarding.md'", report)


if __name__ == "__main__":
    unittest.main()