"""Embed a query and retrieve top-k source chunks from the Chroma corpus index."""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from openai import OpenAI

from src.embedding_demo import OFFLINE_QUERY_VECTOR, generate_embeddings
from src.index_corpus import DEFAULT_OFFLINE_INDEX_COLLECTION
from src.vector_store import DEFAULT_COLLECTION, DEFAULT_DB_PATH, REQUIRED_CONFIG, connect_vector_store


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUERY = "Can I get a refund for an annual plan within 30 days?"
DEFAULT_K_VALUES = (1, 3)
DEFAULT_REPORT = PROJECT_ROOT / "outputs" / "retrieval-demo.md"


def validate_query_vector(collection: Any, model: str, query_vector: Sequence[float]) -> int:
    """Ensure the query uses the collection's embedding model and vector size."""
    metadata = collection.metadata or {}
    stored_model = metadata.get("embedding_model")
    stored_dimension = metadata.get("vector_dimension")
    if stored_model != model:
        raise ValueError(
            f"query model {model!r} does not match collection model {stored_model!r}"
        )
    if not query_vector or len(query_vector) != stored_dimension:
        raise ValueError(
            f"query dimension {len(query_vector)} does not match collection dimension {stored_dimension}"
        )
    return int(stored_dimension)


def retrieve_top_k(collection: Any, query_vector: Sequence[float], k: int) -> list[dict[str, Any]]:
    """Run Chroma cosine search and return similarity scores with source fields."""
    if k <= 0:
        raise ValueError("k must be positive")
    corpus_records = collection.get(where={"record_type": "corpus_chunk"}, include=[])
    record_count = len(corpus_records["ids"])
    if record_count == 0:
        return []
    response = collection.query(
        query_embeddings=[[float(value) for value in query_vector]],
        n_results=min(k, record_count),
        include=["distances", "documents", "metadatas"],
        where={"record_type": "corpus_chunk"},
    )
    matches: list[dict[str, Any]] = []
    ids = response["ids"][0]
    distances = response["distances"][0]
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    for rank, (record_id, distance, text, metadata) in enumerate(
        zip(ids, distances, documents, metadatas),
        start=1,
    ):
        matches.append(
            {
                "rank": rank,
                "id": record_id,
                "score": 1.0 - float(distance),
                "text": text,
                "metadata": metadata,
            }
        )
    return matches


def render_retrieval_report(
    *,
    query: str,
    model: str,
    dimension: int,
    k_values: Sequence[int],
    results_by_k: dict[int, Sequence[dict[str, Any]]],
) -> str:
    """Render query, k comparison, scores, source text, and metadata."""
    lines = [
        "# Top-k Retrieval Sample",
        "",
        f"Query: {query}",
        f"Embedding model: `{model}` (same model recorded on the document collection)",
        f"Query vector dimension: {dimension}",
        "Search: Chroma cosine distance converted to similarity score (`1 - distance`; higher is more similar).",
        "",
        "## Results by k",
        "",
    ]
    for k in k_values:
        matches = results_by_k[k]
        lines.extend([f"### k = {k}", ""])
        if not matches:
            lines.extend(["No matching chunks found.", ""])
            continue
        for match in matches:
            source = match["metadata"].get("source", "unknown")
            chunk_index = match["metadata"].get("chunk_index", "unknown")
            lines.extend(
                [
                    f"{match['rank']}. Score: {match['score']:.6f} | Source: `{source}` | Chunk: `{chunk_index}`",
                    f"   ID: `{match['id']}`",
                    f"   Text: {match['text']}",
                    f"   Metadata: `{json.dumps(match['metadata'], sort_keys=True)}`",
                    "",
                ]
            )
    lines.extend(
        [
            "## Changing k",
            "",
            "Increasing k returns more ranked candidates for downstream grounding, at the cost of more context to inspect and pass to generation. The same query vector is reused for each k so the result sets are directly comparable.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--k", type=int, nargs="+", default=list(DEFAULT_K_VALUES))
    parser.add_argument("--db-path", type=Path)
    parser.add_argument("--collection")
    parser.add_argument("--offline-fixture", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if any(k <= 0 for k in args.k):
        print("Configuration error: every k value must be positive")
        return 1

    load_dotenv(PROJECT_ROOT / ".env")
    db_path = args.db_path or Path(os.getenv("VECTOR_DB_PATH", str(DEFAULT_DB_PATH)))
    if args.offline_fixture:
        model = "offline-fixture-v2"
        query_vector = list(OFFLINE_QUERY_VECTOR)
        collection_name = args.collection or os.getenv(
            "VECTOR_DB_OFFLINE_INDEX_COLLECTION", DEFAULT_OFFLINE_INDEX_COLLECTION
        )
    else:
        missing = [key for key in REQUIRED_CONFIG if not os.getenv(key)]
        if missing:
            print("Configuration error: missing .env values: " + ", ".join(missing))
            return 1
        model = os.environ["EMBEDDING_MODEL"]
        client = OpenAI(base_url=os.environ["API_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"])
        query_vector = generate_embeddings((args.query,), client, model)[0]
        collection_name = args.collection or os.getenv("VECTOR_DB_COLLECTION", DEFAULT_COLLECTION)

    vector_client = None
    try:
        vector_client, _ = connect_vector_store(db_path)
        collection = vector_client.get_collection(collection_name)
        dimension = validate_query_vector(collection, model, query_vector)
        results_by_k = {k: retrieve_top_k(collection, query_vector, k) for k in args.k}
        rendered = render_retrieval_report(
            query=args.query,
            model=model,
            dimension=dimension,
            k_values=args.k,
            results_by_k=results_by_k,
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        print(f"Retrieval report: {args.report}")
        return 0
    except (OSError, RuntimeError, ValueError, LookupError) as error:
        print(f"Retrieval failed: {error}")
        return 1
    finally:
        if vector_client is not None:
            vector_client.close()


if __name__ == "__main__":
    raise SystemExit(main())