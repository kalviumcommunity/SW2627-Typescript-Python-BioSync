"""Offline checks for batch embedding, retry, accounting, and cache behavior."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.batch_embedding import run_batch_embedding
from src.batch_embedding import OfflineEmbeddingClient
from src.embedding_demo import OFFLINE_VECTORS


class FakeEmbeddingClient:
    def __init__(self, failures: int = 0, always_fail: bool = False) -> None:
        self.failures = failures
        self.always_fail = always_fail
        self.calls: list[list[str]] = []

    class _Embeddings:
        def __init__(self, owner: "FakeEmbeddingClient") -> None:
            self.owner = owner

        def create(self, *, input: list[str], model: str) -> SimpleNamespace:
            self.owner.calls.append(input)
            if self.owner.always_fail or self.owner.failures:
                if self.owner.failures:
                    self.owner.failures -= 1
                raise ConnectionError("temporary connection issue")
            data = [
                SimpleNamespace(index=index, embedding=[float(len(text)), 1.0])
                for index, text in enumerate(input)
            ]
            return SimpleNamespace(data=data)

    @property
    def embeddings(self) -> "FakeEmbeddingClient._Embeddings":
        return self._Embeddings(self)


class BatchEmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temporary_directory.name) / "cache.json"
        self.chunks = [
            {"text": f"chunk text {index}", "metadata": {"source": "sample.txt", "chunk_index": index}}
            for index in range(5)
        ]

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_chunks_are_embedded_in_configured_batch_sizes_and_cost_is_reported(self) -> None:
        client = FakeEmbeddingClient()

        summary, results = run_batch_embedding(
            self.chunks,
            client,
            "test-model",
            self.cache_path,
            batch_size=2,
            cost_per_million_tokens=1.0,
            token_counter=lambda _: 10,
        )

        self.assertEqual([len(batch) for batch in client.calls], [2, 2, 1])
        self.assertEqual(summary.total_chunks, 5)
        self.assertEqual(summary.embeddings_generated, 5)
        self.assertEqual(summary.batches_submitted, 3)
        self.assertEqual(summary.estimated_tokens, 50)
        self.assertAlmostEqual(summary.estimated_cost_usd, 0.00005)
        self.assertEqual(len(results), 5)

    def test_transient_failure_retries_with_backoff_then_succeeds(self) -> None:
        client = FakeEmbeddingClient(failures=1)
        delays: list[float] = []

        summary, _ = run_batch_embedding(
            self.chunks[:2],
            client,
            "test-model",
            self.cache_path,
            batch_size=2,
            backoff_base_seconds=2.0,
            sleep=delays.append,
            jitter=lambda: 0.0,
        )

        self.assertEqual(len(client.calls), 2)
        self.assertEqual(delays, [1.0])
        self.assertEqual(summary.retry_attempts, 1)
        self.assertEqual(summary.failed_batches, 0)
        self.assertEqual(summary.embeddings_generated, 2)

    def test_exhausted_batch_is_reported_and_other_batches_continue(self) -> None:
        class FailsFirstBatch(FakeEmbeddingClient):
            class _Embeddings(FakeEmbeddingClient._Embeddings):
                def create(self, *, input: list[str], model: str) -> SimpleNamespace:
                    self.owner.calls.append(input)
                    if len(self.owner.calls) <= 2:
                        raise ConnectionError("still unavailable")
                    return SimpleNamespace(
                        data=[
                            SimpleNamespace(index=index, embedding=[1.0, 2.0])
                            for index, _ in enumerate(input)
                        ]
                    )

            @property
            def embeddings(self) -> "FailsFirstBatch._Embeddings":
                return self._Embeddings(self)

        client = FailsFirstBatch()

        summary, results = run_batch_embedding(
            self.chunks[:3],
            client,
            "test-model",
            self.cache_path,
            batch_size=2,
            max_retries=1,
            sleep=lambda _: None,
            jitter=lambda: 0.0,
        )

        self.assertEqual(summary.failed_batches, 1)
        self.assertEqual(summary.failed_chunks, 2)
        self.assertEqual(summary.retry_attempts, 1)
        self.assertEqual(summary.embeddings_generated, 1)
        self.assertEqual(len(results), 1)
        self.assertTrue(summary.errors)

    def test_rerun_skips_cached_chunks_without_api_calls(self) -> None:
        client = FakeEmbeddingClient()

        first_summary, _ = run_batch_embedding(
            self.chunks[:3], client, "test-model", self.cache_path, batch_size=2
        )
        second_summary, results = run_batch_embedding(
            self.chunks[:3], client, "test-model", self.cache_path, batch_size=2
        )

        self.assertEqual(first_summary.embeddings_generated, 3)
        self.assertEqual(second_summary.embeddings_generated, 0)
        self.assertEqual(second_summary.skipped_chunks, 3)
        self.assertEqual(second_summary.batches_submitted, 0)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(len(results), 3)

    def test_offline_fixture_vectors_follow_text_not_batch_position(self) -> None:
        client = OfflineEmbeddingClient()

        response = client.embeddings.create(
            input=[
                "Use the account email during onboarding.",
                "Customers can ask for a refund.",
                "Annual plan refunds are available within 30 days.",
            ],
            model="offline-fixture-v2",
        )

        self.assertEqual(
            [item.embedding for item in response.data],
            [OFFLINE_VECTORS[2], OFFLINE_VECTORS[1], OFFLINE_VECTORS[0]],
        )


if __name__ == "__main__":
    unittest.main()