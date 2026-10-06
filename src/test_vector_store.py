"""Local Chroma integration checks for schema, persistence, and readback."""

import tempfile
import unittest
from pathlib import Path

import chromadb

from src.vector_store import (
    connect_vector_store,
    get_dimension_checked_collection,
    read_record,
    render_readback_report,
    upsert_record,
)


class VectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "chroma"
        self.clients = []

    def open_client(self):
        client, heartbeat = connect_vector_store(self.db_path)
        self.clients.append(client)
        return client, heartbeat

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.temporary_directory.cleanup()

    def test_client_is_reachable_and_insert_is_read_back_after_reopen(self) -> None:
        client, heartbeat = self.open_client()
        self.assertIsInstance(heartbeat, int)
        collection = get_dimension_checked_collection(client, "readback", "test-model", 3)
        upsert_record(
            collection,
            record_id="sample-record",
            embedding=[0.1, 0.2, 0.3],
            text="A source chunk for retrieval.",
            metadata={"source": "policy.txt", "section": "refunds", "chunk_index": 2},
        )

        reopened_client = chromadb.PersistentClient(path=str(self.db_path))
        self.clients.append(reopened_client)
        record = read_record(reopened_client.get_collection("readback"), "sample-record")

        self.assertEqual(record["id"], "sample-record")
        self.assertEqual(record["vector_length"], 3)
        self.assertEqual(record["text"], "A source chunk for retrieval.")
        self.assertEqual(record["metadata"]["source"], "policy.txt")
        self.assertEqual(record["metadata"]["section"], "refunds")

    def test_collection_records_cosine_model_and_vector_dimension(self) -> None:
        client, _ = self.open_client()

        collection = get_dimension_checked_collection(client, "schema", "test-model", 3)

        self.assertEqual(collection.metadata["hnsw:space"], "cosine")
        self.assertEqual(collection.metadata["embedding_model"], "test-model")
        self.assertEqual(collection.metadata["vector_dimension"], 3)

    def test_existing_collection_rejects_dimension_or_model_mismatch(self) -> None:
        client, _ = self.open_client()
        get_dimension_checked_collection(client, "schema", "test-model", 3)

        with self.assertRaisesRegex(ValueError, "dimension mismatch"):
            get_dimension_checked_collection(client, "schema", "test-model", 4)
        with self.assertRaisesRegex(ValueError, "model mismatch"):
            get_dimension_checked_collection(client, "schema", "other-model", 3)

    def test_chroma_metadata_rejects_null_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be null"):
            upsert_record(
                object(),
                record_id="bad-metadata",
                embedding=[0.1, 0.2],
                text="Text",
                metadata={"source": None},  # type: ignore[dict-item]
            )

    def test_readback_report_uses_portable_project_relative_path(self) -> None:
        report = render_readback_report(
            db_path=Path("outputs") / "chroma",
            collection_name="sample",
            model="test-model",
            heartbeat=123,
            record={
                "id": "sample-record",
                "vector_length": 2,
                "text": "A source chunk.",
                "metadata": {"source": "policy.txt"},
                "embedding": [0.1, 0.2],
            },
        )

        self.assertIn("Local path: `outputs/chroma`", report)


if __name__ == "__main__":
    unittest.main()