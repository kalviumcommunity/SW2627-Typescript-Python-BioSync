"""Batch corpus embeddings with retry handling and a persistent local cache."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time
from typing import Any, Callable, Sequence

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from src.document_loader import load_corpus
from src.token_chunking import token_chunks


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BATCH_SIZE = 64
DEFAULT_MAX_RETRIES = 3
DEFAULT_COST_PER_MILLION_TOKENS = 0.02
DEFAULT_CACHE_PATH = PROJECT_ROOT / "outputs" / "embedding-cache.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "batch-embedding-summary.json"
RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class BatchEmbeddingError(Exception):
    """A failed batch with the number of transient retries already attempted."""

    def __init__(self, error: Exception, attempts: int) -> None:
        super().__init__(str(error))
        self.error = error
        self.attempts = attempts


@dataclass(frozen=True)
class BatchRunSummary:
    total_chunks: int
    embeddings_generated: int
    skipped_chunks: int
    failed_chunks: int
    failed_batches: int
    batches_submitted: int
    retry_attempts: int
    estimated_tokens: int
    estimated_cost_usd: float
    batch_size: int
    max_retries: int
    model: str
    errors: tuple[str, ...]


def chunk_key(model: str, text: str) -> str:
    """Use model plus exact chunk text so model changes invalidate cached vectors."""
    return hashlib.sha256(f"{model}\0{text}".encode("utf-8")).hexdigest()


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    """Read cached embeddings, treating an absent cache as empty."""
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("embedding cache must contain a JSON object")
    return payload


def save_cache(path: Path, cache: dict[str, dict[str, Any]]) -> None:
    """Atomically replace cache so interrupted runs do not leave partial JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(cache, temporary_file, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _retryable(error: Exception) -> bool:
    if isinstance(error, (RateLimitError, APIConnectionError, TimeoutError, ConnectionError)):
        return True
    return isinstance(error, APIStatusError) and error.status_code in RETRYABLE_STATUS_CODES


def _error_message(error: Exception) -> str:
    if isinstance(error, APIStatusError):
        return f"HTTP {error.status_code}: {error.message}"
    return f"{type(error).__name__}: {error}"


def embed_batch_with_retries(
    texts: Sequence[str],
    client: Any,
    model: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_base_seconds: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    jitter: Callable[[], float] = random.random,
) -> tuple[list[list[float]], int]:
    """Request one batch and exponentially back off for transient failures."""
    attempt = 0
    while True:
        try:
            response = client.embeddings.create(input=list(texts), model=model)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors = [list(item.embedding) for item in ordered]
            if len(vectors) != len(texts):
                raise ValueError("embedding provider returned the wrong number of vectors")
            dimensions = {len(vector) for vector in vectors}
            if not dimensions or 0 in dimensions or len(dimensions) != 1:
                raise ValueError("embedding provider returned inconsistent vector dimensions")
            return vectors, attempt
        except Exception as error:
            if not _retryable(error) or attempt >= max_retries:
                raise BatchEmbeddingError(error, attempt) from error
            delay = backoff_base_seconds * (2**attempt) * (0.5 + jitter())
            sleep(delay)
            attempt += 1


def run_batch_embedding(
    chunks: Sequence[dict[str, Any]],
    client: Any,
    model: str,
    cache_path: Path,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_base_seconds: float = 1.0,
    cost_per_million_tokens: float = DEFAULT_COST_PER_MILLION_TOKENS,
    token_counter: Callable[[str], int] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    jitter: Callable[[], float] = random.random,
) -> tuple[BatchRunSummary, list[dict[str, Any]]]:
    """Embed uncached chunks in bounded batches and persist successful vectors."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    if cost_per_million_tokens < 0:
        raise ValueError("cost_per_million_tokens cannot be negative")
    token_counter = token_counter or (lambda text: max(1, (len(text) + 3) // 4))
    cache = load_cache(cache_path)
    pending: list[tuple[str, dict[str, Any]]] = []
    skipped = 0
    scheduled: set[str] = set()
    for chunk in chunks:
        key = chunk_key(model, chunk["text"])
        cached = cache.get(key)
        if cached and cached.get("model") == model and cached.get("text") == chunk["text"] and cached.get("embedding"):
            skipped += 1
        elif key in scheduled:
            skipped += 1
        else:
            pending.append((key, chunk))
            scheduled.add(key)

    generated = 0
    failed_chunks = 0
    failed_batches = 0
    submitted_batches = 0
    retry_attempts = 0
    estimated_tokens = 0
    errors: list[str] = []

    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        texts = [chunk["text"] for _, chunk in batch]
        submitted_batches += 1
        estimated_tokens += sum(token_counter(text) for text in texts)
        try:
            vectors, retries = embed_batch_with_retries(
                texts,
                client,
                model,
                max_retries=max_retries,
                backoff_base_seconds=backoff_base_seconds,
                sleep=sleep,
                jitter=jitter,
            )
            retry_attempts += retries
            for (key, chunk), vector in zip(batch, vectors):
                cache[key] = {
                    "model": model,
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                    "embedding": vector,
                }
            generated += len(batch)
            save_cache(cache_path, cache)
        except Exception as error:
            failed_batches += 1
            failed_chunks += len(batch)
            retry_attempts += getattr(error, "attempts", 0)
            root_error = error.error if isinstance(error, BatchEmbeddingError) else error
            errors.append(f"batch {submitted_batches} ({len(batch)} chunk(s)): {_error_message(root_error)}")

    summary = BatchRunSummary(
        total_chunks=len(chunks),
        embeddings_generated=generated,
        skipped_chunks=skipped,
        failed_chunks=failed_chunks,
        failed_batches=failed_batches,
        batches_submitted=submitted_batches,
        retry_attempts=retry_attempts,
        estimated_tokens=estimated_tokens,
        estimated_cost_usd=estimated_tokens * cost_per_million_tokens / 1_000_000,
        batch_size=batch_size,
        max_retries=max_retries,
        model=model,
        errors=tuple(errors),
    )
    results = [
        {
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "embedding": cache.get(chunk_key(model, chunk["text"]), {}).get("embedding"),
        }
        for chunk in chunks
        if chunk_key(model, chunk["text"]) in cache
    ]
    return summary, results


def render_summary(summary: BatchRunSummary, *, offline: bool = False) -> str:
    """Serialize a reviewer-friendly run summary."""
    return json.dumps(
        {
            "run_mode": "offline fixture" if offline else "embedding API",
            "total_chunks": summary.total_chunks,
            "embeddings_generated": summary.embeddings_generated,
            "skipped_chunks": summary.skipped_chunks,
            "failed_chunks": summary.failed_chunks,
            "failed_batches": summary.failed_batches,
            "batches_submitted": summary.batches_submitted,
            "retry_attempts": summary.retry_attempts,
            "batch_size": summary.batch_size,
            "max_retries": summary.max_retries,
            "retry_policy": "exponential backoff for rate limits and transient connection/HTTP failures",
            "model": summary.model,
            "estimated_tokens": summary.estimated_tokens,
            "estimated_cost_usd": round(summary.estimated_cost_usd, 8),
            "cost_note": "Approximate: token count uses a local estimate unless a model tokenizer counter is supplied; rate is configurable.",
            "errors": list(summary.errors),
        },
        indent=2,
    ) + "\n"


class OfflineEmbeddingClient:
    """Deterministic client for demonstrating batching and cache reuse offline."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    class _Embeddings:
        def __init__(self, owner: "OfflineEmbeddingClient") -> None:
            self.owner = owner

        def create(self, *, input: list[str], model: str) -> Any:
            from src.embedding_demo import OFFLINE_VECTORS

            self.owner.calls.append(input)
            vectors = []
            for index, text in enumerate(input):
                vector = OFFLINE_VECTORS[index % len(OFFLINE_VECTORS)]
                vectors.append(type("Embedding", (), {"index": index, "embedding": vector})())
            return type("Response", (), {"data": vectors})()

    @property
    def embeddings(self) -> "OfflineEmbeddingClient._Embeddings":
        return self._Embeddings(self)


def load_corpus_chunks() -> list[dict[str, Any]]:
    """Load, clean, and token-chunk every supported sample corpus document."""
    corpus = PROJECT_ROOT / "data" / "sample-corpus"
    documents = load_corpus(sorted(corpus.iterdir()))
    return [
        {"text": chunk.text, "metadata": dict(chunk.metadata)}
        for document in documents
        for chunk in token_chunks(document)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--cost-per-million-tokens", type=float, default=DEFAULT_COST_PER_MILLION_TOKENS)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--offline-fixture", action="store_true")
    args = parser.parse_args()

    try:
        chunks = load_corpus_chunks()
        if args.offline_fixture:
            client: Any = OfflineEmbeddingClient()
            model = "offline-fixture-v1"
        else:
            load_dotenv(PROJECT_ROOT / ".env")
            missing = [key for key in ("API_BASE_URL", "OPENAI_API_KEY", "EMBEDDING_MODEL") if not os.getenv(key)]
            if missing:
                raise RuntimeError("Missing required .env values: " + ", ".join(missing))
            model = os.environ["EMBEDDING_MODEL"]
            client = OpenAI(base_url=os.environ["API_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"])

        summary, results = run_batch_embedding(
            chunks,
            client,
            model,
            args.cache,
            batch_size=args.batch_size,
            max_retries=args.max_retries,
            cost_per_million_tokens=args.cost_per_million_tokens,
        )
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(render_summary(summary, offline=args.offline_fixture), encoding="utf-8")
        print(render_summary(summary, offline=args.offline_fixture), end="")
        print(f"Cached embeddings available for {len(results)} chunk(s). Summary: {args.summary}")
        return 1 if summary.failed_chunks else 0
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Batch embedding failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())