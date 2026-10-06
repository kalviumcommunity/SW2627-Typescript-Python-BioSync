"""Configure a persistent Chroma collection and verify an insert/readback."""

import argparse
import json
import os
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from src.embedding_demo import OFFLINE_QUERY_VECTOR, generate_embeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "outputs" / "chroma"
DEFAULT_COLLECTION = "sprint_2_chunks"
DEFAULT_OFFLINE_COLLECTION = "sprint_2_chunks_offline_fixture"
DEFAULT_TEST_ID = "vector-db-readback-test"
TEST_TEXT = "Annual plans can be refunded within 30 days."
TEST_METADATA: dict[str, str | int] = {
    "source": "policy.txt",
    "section": "refunds",
    "chunk_index": 1,
    "page": 1,
}
REQUIRED_CONFIG = ("API_BASE_URL", "OPENAI_API_KEY", "EMBEDDING_MODEL")


def connect_vector_store(path: Path) -> tuple[Any, int]:
    """Open the local persistent database and return a successful heartbeat."""
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    heartbeat = client.heartbeat()
    if not isinstance(heartbeat, int):
        raise RuntimeError("ChromaDB did not return a valid heartbeat")
    return client, heartbeat


def get_dimension_checked_collection(
    client: Any,
    name: str,
    model: str,
    dimension: int,
) -> Any:
    """Create a cosine collection or reject an existing incompatible schema."""
    if dimension <= 0:
        raise ValueError("embedding dimension must be positive")
    collection = client.get_or_create_collection(
        name=name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": model,
            "vector_dimension": dimension,
        },
    )
    metadata = collection.metadata or {}
    stored_dimension = metadata.get("vector_dimension")
    stored_model = metadata.get("embedding_model")
    if stored_dimension != dimension:
        raise ValueError(
            f"collection {name!r} dimension mismatch: stored={stored_dimension}, requested={dimension}"
        )
    if stored_model != model:
        raise ValueError(
            f"collection {name!r} model mismatch: stored={stored_model!r}, requested={model!r}"
        )
    if metadata.get("hnsw:space") != "cosine":
        raise ValueError(f"collection {name!r} must use cosine distance")
    return collection


def upsert_record(
    collection: Any,
    *,
    record_id: str,
    embedding: list[float],
    text: str,
    metadata: dict[str, str | int | float | bool],
) -> None:
    """Store a vector, its source text, and non-null scalar metadata."""
    if not record_id.strip() or not text.strip():
        raise ValueError("record ID and source text must be non-empty")
    if not embedding or any(not isinstance(value, (int, float)) for value in embedding):
        raise ValueError("embedding must be a non-empty numeric vector")
    if any(value is None for value in metadata.values()):
        raise ValueError("Chroma metadata values cannot be null")
    upsert = getattr(collection, "upsert", None)
    if upsert is None:
        raise RuntimeError("Chroma collection does not support upsert")
    upsert(
        ids=[record_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata],
    )


def read_record(collection: Any, record_id: str) -> dict[str, Any]:
    """Read back a record and validate its required fields."""
    result = collection.get(ids=[record_id], include=["embeddings", "documents", "metadatas"])
    if not result["ids"]:
        raise LookupError(f"record {record_id!r} was not found after insert")
    embedding = result["embeddings"][0]
    record = {
        "id": result["ids"][0],
        "vector_length": len(embedding),
        "text": result["documents"][0],
        "metadata": result["metadatas"][0],
        "embedding": [float(value) for value in embedding],
    }
    if not record["text"] or not record["metadata"]:
        raise ValueError("readback record is missing text or metadata")
    return record


def render_readback_report(
    *,
    db_path: Path,
    collection_name: str,
    model: str,
    heartbeat: int,
    record: dict[str, Any],
) -> str:
    """Render a compact evidence report without dumping a large vector."""
    try:
        display_path = db_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        display_path = "custom local path"
    return "\n".join(
        [
            "# Vector Store Insert/Readback",
            "",
            "Database: ChromaDB PersistentClient",
            f"Reachable: yes (heartbeat: {heartbeat})",
            f"Local path: `{display_path}`",
            f"Collection: `{collection_name}`",
            "Distance metric: cosine",
            f"Embedding model: `{model}`",
            f"Collection dimension: {record['vector_length']}",
            "",
            "## Read-back record",
            "",
            f"ID: `{record['id']}`",
            f"Vector length: {record['vector_length']}",
            f"Text: {record['text']}",
            f"Metadata: `{json.dumps(record['metadata'], sort_keys=True)}`",
            f"Vector sample: `{record['embedding'][:8]}`",
            "",
            "The vector is stored as the collection embedding, the source text as its document, and citation fields as scalar metadata.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path)
    parser.add_argument("--collection")
    parser.add_argument("--offline-fixture", action="store_true")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "outputs" / "vector-db-readback.md")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    db_path = args.db_path or Path(os.getenv("VECTOR_DB_PATH", str(DEFAULT_DB_PATH)))

    if args.offline_fixture:
        model = "offline-fixture-v1"
        vector = list(OFFLINE_QUERY_VECTOR)
        collection_name = args.collection or os.getenv(
            "VECTOR_DB_OFFLINE_COLLECTION", DEFAULT_OFFLINE_COLLECTION
        )
    else:
        collection_name = args.collection or os.getenv("VECTOR_DB_COLLECTION", DEFAULT_COLLECTION)
        missing = [key for key in REQUIRED_CONFIG if not os.getenv(key)]
        if missing:
            print("Configuration error: missing .env values: " + ", ".join(missing))
            return 1
        model = os.environ["EMBEDDING_MODEL"]
        client = OpenAI(base_url=os.environ["API_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"])
        vector = generate_embeddings((TEST_TEXT,), client, model)[0]

    try:
        vector_client, heartbeat = connect_vector_store(db_path)
        collection = get_dimension_checked_collection(vector_client, collection_name, model, len(vector))
        upsert_record(
            collection,
            record_id=DEFAULT_TEST_ID,
            embedding=vector,
            text=TEST_TEXT,
            metadata=TEST_METADATA,
        )
        record = read_record(collection, DEFAULT_TEST_ID)
        if record["vector_length"] != len(vector):
            raise ValueError("read-back vector dimension does not match inserted vector")
        rendered = render_readback_report(
            db_path=db_path,
            collection_name=collection_name,
            model=model,
            heartbeat=heartbeat,
            record=record,
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        print(f"Readback verified. Report: {args.report}")
        return 0
    except (OSError, RuntimeError, ValueError, LookupError) as error:
        print(f"Vector store check failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())