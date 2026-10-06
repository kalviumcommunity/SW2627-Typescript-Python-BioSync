"""Generate embeddings and compare their semantic similarity."""

import argparse
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = ("API_BASE_URL", "OPENAI_API_KEY", "EMBEDDING_MODEL")
SAMPLE_TEXTS = (
    "annual plan refunds are available within thirty days",
    "customers can request a refund for an annual plan within 30 days",
    "the office cafeteria serves soup on Thursdays",
)
SAMPLE_QUERY = "Can I get a refund for my annual subscription within 30 days?"
SAMPLE_CHUNKS = (
    {
        "text": SAMPLE_TEXTS[0],
        "metadata": {"source": "policy.txt", "section": "refunds", "chunk_index": 1, "page": 1},
    },
    {
        "text": SAMPLE_TEXTS[1],
        "metadata": {"source": "faq.html", "section": "refunds", "chunk_index": 2, "page": None},
    },
    {
        "text": SAMPLE_TEXTS[2],
        "metadata": {"source": "onboarding.md", "section": "facilities", "chunk_index": 1, "page": None},
    },
)

# Small, deterministic vectors let the report and tests run without an API key.
OFFLINE_VECTORS = (
    (0.91, 0.12, 0.24, 0.08, 0.03, 0.11, 0.18, 0.07),
    (0.88, 0.16, 0.27, 0.10, 0.04, 0.13, 0.17, 0.09),
    (0.05, 0.82, 0.09, 0.71, 0.18, 0.03, 0.12, 0.66),
)
OFFLINE_QUERY_VECTOR = (0.90, 0.14, 0.255, 0.09, 0.035, 0.12, 0.175, 0.08)


@dataclass(frozen=True)
class StoredEmbedding:
    """An embedding stored with the source needed to cite it during retrieval."""

    text: str
    metadata: dict[str, str | int | None]
    vector: list[float]


def cosine_similarity(first: Sequence[float], second: Sequence[float]) -> float:
    """Return cosine similarity for two same-length non-zero vectors."""
    if len(first) != len(second) or not first:
        raise ValueError("vectors must be non-empty and have the same length")
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        raise ValueError("cosine similarity is undefined for a zero vector")
    return sum(left * right for left, right in zip(first, second)) / (first_norm * second_norm)


def load_config() -> tuple[str, str, str]:
    """Load the OpenAI-compatible endpoint, key, and embedding model."""
    load_dotenv(PROJECT_ROOT / ".env")
    missing_keys = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    if missing_keys:
        raise RuntimeError("Missing required .env values: " + ", ".join(missing_keys))
    return os.environ["API_BASE_URL"], os.environ["OPENAI_API_KEY"], os.environ["EMBEDDING_MODEL"]


def generate_embeddings(texts: Sequence[str], client: Any, model: str) -> list[list[float]]:
    """Generate one embedding vector for every input text."""
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("texts must contain at least one non-empty string")
    response = client.embeddings.create(input=list(texts), model=model)
    ordered_data = sorted(response.data, key=lambda item: item.index)
    vectors = [list(item.embedding) for item in ordered_data]
    if len(vectors) != len(texts):
        raise ValueError("embedding provider returned the wrong number of vectors")
    dimension = len(vectors[0])
    if dimension == 0 or any(len(vector) != dimension for vector in vectors):
        raise ValueError("embedding provider returned inconsistent vector dimensions")
    return vectors


def embed_chunks(
    chunks: Sequence[dict[str, Any]], client: Any, model: str
) -> list[StoredEmbedding]:
    """Embed prepared chunks and preserve each chunk's text and metadata."""
    texts = [chunk["text"] for chunk in chunks]
    vectors = generate_embeddings(texts, client, model)
    return [
        StoredEmbedding(text=chunk["text"], metadata=dict(chunk["metadata"]), vector=vector)
        for chunk, vector in zip(chunks, vectors)
    ]


def stored_embeddings_from_vectors(
    chunks: Sequence[dict[str, Any]], vectors: Sequence[Sequence[float]]
) -> list[StoredEmbedding]:
    """Build storage records for deterministic offline demonstration output."""
    if len(chunks) != len(vectors):
        raise ValueError("the number of chunks must match the number of vectors")
    return [
        StoredEmbedding(text=chunk["text"], metadata=dict(chunk["metadata"]), vector=list(vector))
        for chunk, vector in zip(chunks, vectors)
    ]


def rank_chunks(
    query_vector: Sequence[float], records: Sequence[StoredEmbedding]
) -> list[tuple[float, StoredEmbedding]]:
    """Return chunks ordered from highest to lowest cosine similarity to a query."""
    return sorted(
        ((cosine_similarity(query_vector, record.vector), record) for record in records),
        key=lambda result: result[0],
        reverse=True,
    )


def render_similarity_report(
    query: str,
    query_vector: Sequence[float],
    records: Sequence[StoredEmbedding],
    source: str,
) -> str:
    """Render ranked chunk evidence, including the best and weakest matches."""
    ranked = rank_chunks(query_vector, records)
    if not ranked:
        raise ValueError("at least one stored embedding is required")
    lines = [
        "# Similarity Ranking",
        "",
        f"Embedding source: {source}",
        f"Query: {query}",
        "Metric: cosine similarity (higher scores indicate more aligned vector directions).",
        "",
        "Cosine similarity compares vector direction rather than magnitude, making it a useful ranking score for text embeddings. It is a similarity, not a distance: higher is closer in meaning according to the embedding model. A high score is not proof that a chunk is correct or sufficient.",
        "",
        "## Ranked chunks",
        "",
    ]
    for rank, (score, record) in enumerate(ranked, start=1):
        lines.extend(
            [
                f"### {rank}. Cosine similarity: {score:.4f}",
                "",
                f"Text: {record.text}",
                f"Metadata: `{record.metadata}`",
                "",
            ]
        )
    most_score, most_record = ranked[0]
    least_score, least_record = ranked[-1]
    lines.extend(
        [
            "## Most similar",
            "",
            f"{most_record.text} (score: {most_score:.4f}; source: {most_record.metadata['source']})",
            "",
            "## Least similar",
            "",
            f"{least_record.text} (score: {least_score:.4f}; source: {least_record.metadata['source']})",
            "",
            "The highest-ranked chunk is the first retrieval candidate; the score orders candidates but does not independently verify their claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report(texts: Sequence[str], vectors: Sequence[Sequence[float]], source: str) -> str:
    """Render dimensions, comparisons, and trimmed vectors for inspection."""
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1:
        raise ValueError("all vectors must have the same dimension")
    similar_score = cosine_similarity(vectors[0], vectors[1])
    dissimilar_score = cosine_similarity(vectors[0], vectors[2])
    lines = [
        "# Embedding Demonstration",
        "",
        f"Source: {source}",
        "",
        f"Sample texts: {len(texts)}",
        f"Vector dimension: {len(vectors[0])}",
        f"All vectors same length: {len(dimensions) == 1}",
        "",
        "## Similarity comparison",
        "",
        f"Similar pair (texts 1 and 2): {similar_score:.4f}",
        f"Dissimilar pair (texts 1 and 3): {dissimilar_score:.4f}",
        f"Similar pair scores higher: {similar_score > dissimilar_score}",
        "",
        "## Sample vector output",
        "",
        "Only the first 8 values are shown below; production embeddings are longer.",
    ]
    for index, (text, vector) in enumerate(zip(texts, vectors), start=1):
        lines.append(f"{index}. {text}")
        lines.append(f"   [{', '.join(f'{value:.4f}' for value in vector[:8])}, ...]")
    lines.extend(
        [
            "",
            "## What the vectors represent",
            "",
            "An embedding vector is a numeric representation of a piece of text's meaning, learned from language patterns. It is not a random ID and it is not a count of keywords. Texts with related meanings tend to occupy nearby regions in vector space, which lets retrieval find relevant passages even when the query and passage use different words.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_storage_report(records: Sequence[StoredEmbedding], source: str) -> str:
    """Render stored chunk text, metadata, vector length, and sample values."""
    if not records:
        raise ValueError("at least one stored embedding is required")
    dimensions = {len(record.vector) for record in records}
    if len(dimensions) != 1 or not dimensions:
        raise ValueError("all stored vectors must have the same dimension")
    lines = [
        "# Stored Chunk Embeddings",
        "",
        f"Source: {source}",
        f"Chunks embedded: {len(records)}",
        f"Vector length: {len(records[0].vector)}",
        f"Every stored vector has the expected length: {len(dimensions) == 1}",
        "",
        "## Stored records",
        "",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"### Record {index}",
                "",
                f"Text: {record.text}",
                f"Metadata: `{record.metadata}`",
                f"Vector length: {len(record.vector)}",
                f"Vector sample: [{', '.join(f'{value:.4f}' for value in record.vector[:8])}, ...]",
                "",
            ]
        )
    lines.extend(
        [
            "## Retrieval note",
            "",
            "Each vector remains attached to its original chunk text and metadata, so a similarity search can return the matching passage together with its source document, section, and chunk index.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    """Run the live embedding demo, or a reproducible offline fixture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-fixture", action="store_true", help="use local sample vectors without an API request")
    args = parser.parse_args()

    try:
        if args.offline_fixture:
            records = stored_embeddings_from_vectors(SAMPLE_CHUNKS, OFFLINE_VECTORS)
            query_vector = OFFLINE_QUERY_VECTOR
            source = "offline fixture (no API request)"
        else:
            base_url, api_key, model = load_config()
            client = OpenAI(base_url=base_url, api_key=api_key)
            records = embed_chunks(SAMPLE_CHUNKS, client, model)
            query_vector = generate_embeddings((SAMPLE_QUERY,), client, model)[0]
            source = f"API model {model}"
        print(render_storage_report(records, source))
        print(render_similarity_report(SAMPLE_QUERY, query_vector, records, source))
        return 0
    except (AuthenticationError, RateLimitError, APIConnectionError) as error:
        print(f"Embedding request failed: {error}")
        return 1
    except APIStatusError as error:
        print(f"Embedding request failed ({error.status_code}): {error.message}")
        return 1
    except RuntimeError as error:
        print(f"Configuration error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())