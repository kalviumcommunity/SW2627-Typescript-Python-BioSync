"""Embed and index every sample-corpus chunk into a persistent Chroma collection."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from openai import OpenAI

from src.batch_embedding import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CACHE_PATH,
    OfflineEmbeddingClient,
    load_corpus_chunks,
    run_batch_embedding,
)
from src.embedding_demo import generate_embeddings
from src.vector_store import (
    DEFAULT_COLLECTION,
    DEFAULT_DB_PATH,
    DEFAULT_OFFLINE_COLLECTION,
    REQUIRED_CONFIG,
    connect_vector_store,
    get_dimension_checked_collection,
    read_record,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_REPORT = PROJECT_ROOT / "outputs" / "corpus-index-summary.md"
DEFAULT_OFFLINE_INDEX_COLLECTION = "sprint_2_corpus_offline_fixture_v2"
DEFAULT_INDEX_BATCH_SIZE = 128


def _identity_payload(text: str, metadata: dict[str, Any]) -> str:
    identity = {
        "source": metadata.get("source"),
        "chunk_index": metadata.get("chunk_index"),
        "position_start": metadata.get("position_start"),
        "position_end": metadata.get("position_end"),
        "text": text,
    }
    return json.dumps(identity, sort_keys=True, ensure_ascii=True)


def corpus_record_id(text: str, metadata: dict[str, Any]) -> str:
    """Build a stable record ID from source identity and exact chunk content."""
    return hashlib.sha256(_identity_payload(text, metadata).encode("utf-8")).hexdigest()


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Drop nullable chunk fields because Chroma metadata accepts scalar values only."""
    return {
        key: value
        for key, value in metadata.items()
        if value is not None and isinstance(value, (str, int, float, bool))
    }


def index_embedded_chunks(
    chunks: Sequence[dict[str, Any]],
    embedded_chunks: Sequence[dict[str, Any]],
    client: Any,
    model: str,
    collection_name: str,
    *,
    batch_size: int = DEFAULT_INDEX_BATCH_SIZE,
    prior_ingestion_count: int | None = None,
) -> dict[str, Any]:
    """Upsert available vectors, reconcile stale corpus rows, count, and spot-check."""
    if batch_size <= 0:
        raise ValueError("index batch size must be positive")
    if not embedded_chunks:
        raise ValueError("no embeddings are available to initialize the collection")
    dimensions = {len(item["embedding"]) for item in embedded_chunks}
    if len(dimensions) != 1 or 0 in dimensions:
        raise ValueError("embedded chunks must all have the same non-zero dimension")
    dimension = dimensions.pop()
    collection = get_dimension_checked_collection(client, collection_name, model, dimension)

    expected_ids = {corpus_record_id(chunk["text"], chunk["metadata"]) for chunk in chunks}
    prepared: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in embedded_chunks:
        record_id = corpus_record_id(item["text"], item["metadata"])
        if record_id not in expected_ids:
            raise ValueError("embedding result does not match a current corpus chunk")
        if record_id in seen_ids:
            raise ValueError("duplicate embedding result for a corpus chunk")
        seen_ids.add(record_id)
        metadata = _chroma_metadata(item["metadata"])
        metadata["record_type"] = "corpus_chunk"
        prepared.append(
            {
                "id": record_id,
                "text": item["text"],
                "metadata": metadata,
                "embedding": [float(value) for value in item["embedding"]],
            }
        )

    upsert_failures: list[str] = []
    inserted_count = 0
    inserted_ids: list[str] = []
    for offset in range(0, len(prepared), batch_size):
        batch = prepared[offset : offset + batch_size]
        try:
            collection.upsert(
                ids=[item["id"] for item in batch],
                embeddings=[item["embedding"] for item in batch],
                documents=[item["text"] for item in batch],
                metadatas=[item["metadata"] for item in batch],
            )
            inserted_count += len(batch)
            inserted_ids.extend(item["id"] for item in batch)
        except Exception as error:
            upsert_failures.append(f"upsert batch {offset // batch_size + 1}: {type(error).__name__}: {error}")

    stale_ids: list[str] = []
    if not upsert_failures and len(prepared) == len(chunks):
        existing = collection.get(where={"record_type": "corpus_chunk"}, include=[])
        stale_ids = [record_id for record_id in existing["ids"] if record_id not in expected_ids]
        if stale_ids:
            collection.delete(ids=stale_ids)

    indexed_records = collection.get(where={"record_type": "corpus_chunk"}, include=[])
    indexed_count = len(indexed_records["ids"])
    failures = list(upsert_failures)
    if len(embedded_chunks) != len(chunks):
        failures.append(f"embeddings available for {len(embedded_chunks)} of {len(chunks)} chunks")

    spot_check: dict[str, Any] | None = None
    spot_check_matches = False
    sample = next((item for item in prepared if item["id"] in inserted_ids), None)
    if sample:
        try:
            stored = read_record(collection, sample["id"])
            spot_check = {
                "id": stored["id"],
                "text": stored["text"],
                "metadata": stored["metadata"],
                "vector_length": stored["vector_length"],
            }
            spot_check_matches = (
                stored["id"] == sample["id"]
                and stored["text"] == sample["text"]
                and stored["metadata"] == sample["metadata"]
                and stored["vector_length"] == dimension
            )
        except Exception as error:
            failures.append(f"spot-check readback failed: {type(error).__name__}: {error}")
    if indexed_count != len(chunks):
        failures.append(f"indexed count {indexed_count} does not match corpus chunk count {len(chunks)}")
    if not spot_check_matches:
        failures.append("spot-check record did not exactly match the source chunk")
    prior_count_matches = prior_ingestion_count is None or prior_ingestion_count == len(chunks)
    if not prior_count_matches:
        failures.append(
            f"current corpus has {len(chunks)} chunks but prior ingestion summary records {prior_ingestion_count}"
        )

    return {
        "collection": collection_name,
        "model": model,
        "dimension": dimension,
        "expected_chunks": len(chunks),
        "prior_ingestion_chunks": prior_ingestion_count,
        "prior_count_matches": prior_count_matches,
        "embeddings_available": len(embedded_chunks),
        "records_upserted": inserted_count,
        "indexed_count": indexed_count,
        "count_matches": indexed_count == len(chunks),
        "stale_records_removed": len(stale_ids),
        "spot_check": spot_check,
        "spot_check_matches": spot_check_matches,
        "failures": failures,
    }


def render_index_report(
    summary: dict[str, Any],
    *,
    db_path: Path,
    heartbeat: int,
    embedding_summary: Any,
) -> str:
    """Format run totals and the exact spot-check result for review."""
    try:
        display_path = db_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        display_path = "custom local path"
    spot = summary["spot_check"] or {}
    lines = [
        "# Corpus Vector Index Summary",
        "",
        "Database: ChromaDB PersistentClient",
        f"Reachable: yes (heartbeat: {heartbeat})",
        f"Local path: `{display_path}`",
        f"Collection: `{summary['collection']}`",
        f"Embedding model: `{summary['model']}`",
        f"Vector dimension: {summary['dimension']}",
        "",
        "## Count validation",
        "",
        f"Corpus chunks expected: {summary['expected_chunks']}",
        f"Prior ingestion summary chunks: {summary['prior_ingestion_chunks'] if summary['prior_ingestion_chunks'] is not None else 'unavailable'}",
        f"Current count matches prior ingestion summary: {'yes' if summary['prior_count_matches'] else 'no'}",
        f"Embeddings available: {summary['embeddings_available']}",
        f"Records upserted this run: {summary['records_upserted']}",
        f"Indexed corpus records: {summary['indexed_count']}",
        f"Count matches: {'yes' if summary['count_matches'] else 'no'}",
        f"Stale corpus records removed: {summary['stale_records_removed']}",
        f"Embedding cache skips: {embedding_summary.skipped_chunks}",
        f"Embedding failures: {embedding_summary.failed_chunks}",
        f"Index failures: {len(summary['failures'])}",
        "",
        "## Spot-check readback",
        "",
        f"Matches source chunk: {'yes' if summary['spot_check_matches'] else 'no'}",
        f"ID: `{spot.get('id', 'unavailable')}`",
        f"Vector length: {spot.get('vector_length', 'unavailable')}",
        f"Text: {spot.get('text', 'unavailable')}",
        f"Metadata: `{json.dumps(spot.get('metadata', {}), sort_keys=True)}`",
        "",
        "The collection stores each embedding as a vector, original chunk text as the document, and source/chunk metadata as scalar fields. IDs are deterministic, so reruns update the same records; stale corpus-tagged IDs are removed only after all current chunks were embedded and upserted successfully.",
        "",
        "## Failures",
        "",
    ]
    lines.extend(f"- {failure}" for failure in summary["failures"] or ["None"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--index-batch-size", type=int, default=DEFAULT_INDEX_BATCH_SIZE)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--db-path", type=Path)
    parser.add_argument("--collection")
    parser.add_argument("--offline-fixture", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_INDEX_REPORT)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    db_path = args.db_path or Path(os.getenv("VECTOR_DB_PATH", str(DEFAULT_DB_PATH)))
    chunks = load_corpus_chunks()
    if not chunks:
        print("No corpus chunks were produced; nothing to index.")
        return 1
    prior_summary_path = PROJECT_ROOT / "docs" / "full-ingestion-summary.json"
    prior_ingestion_count = None
    if prior_summary_path.exists():
        prior_ingestion_count = int(
            json.loads(prior_summary_path.read_text(encoding="utf-8"))["total_chunks_created"]
        )

    if args.offline_fixture:
        model = "offline-fixture-v2"
        embedding_client: Any = OfflineEmbeddingClient()
        collection_name = args.collection or os.getenv(
            "VECTOR_DB_OFFLINE_INDEX_COLLECTION", DEFAULT_OFFLINE_INDEX_COLLECTION
        )
    else:
        missing = [key for key in REQUIRED_CONFIG if not os.getenv(key)]
        if missing:
            print("Configuration error: missing .env values: " + ", ".join(missing))
            return 1
        model = os.environ["EMBEDDING_MODEL"]
        embedding_client = OpenAI(
            base_url=os.environ["API_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        )
        collection_name = args.collection or os.getenv("VECTOR_DB_COLLECTION", DEFAULT_COLLECTION)

    embedding_summary, embedded_chunks = run_batch_embedding(
        chunks,
        embedding_client,
        model,
        args.cache,
        batch_size=args.batch_size,
    )
    if not embedded_chunks:
        print("No embeddings are available; corpus indexing was not started.")
        for error in embedding_summary.errors:
            print(error)
        return 1

    vector_client = None
    try:
        vector_client, heartbeat = connect_vector_store(db_path)
        summary = index_embedded_chunks(
            chunks,
            embedded_chunks,
            vector_client,
            model,
            collection_name,
            batch_size=args.index_batch_size,
            prior_ingestion_count=prior_ingestion_count,
        )
        if embedding_summary.failed_chunks:
            summary["failures"].extend(embedding_summary.errors)
        rendered = render_index_report(
            summary,
            db_path=db_path,
            heartbeat=heartbeat,
            embedding_summary=embedding_summary,
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        print(f"Index report: {args.report}")
        return 0 if not summary["failures"] else 1
    except (OSError, RuntimeError, ValueError, LookupError) as error:
        print(f"Corpus indexing failed: {error}")
        return 1
    finally:
        if vector_client is not None:
            vector_client.close()


if __name__ == "__main__":
    raise SystemExit(main())