# Batch Embedding Sample Run

Command: `python -m src.batch_embedding --offline-fixture --batch-size 2`

The offline fixture makes no API request. It exercises the same batch orchestration and JSON cache path with deterministic vectors. The estimated cost demonstrates the configured default rate of `$0.02` per million tokens; it is not a billable provider measurement.

## First run

| Measure | Result |
| --- | ---: |
| Total chunks | 3 |
| Embeddings generated | 3 |
| Skipped from cache | 0 |
| Failed chunks / batches | 0 / 0 |
| Batches submitted | 2 (batch size 2) |
| Retry attempts | 0 (maximum configured: 3) |
| Estimated tokens | 72 |
| Approximate cost | `$0.00000144` |

## Rerun with the same cache

| Measure | Result |
| --- | ---: |
| Total chunks | 3 |
| Embeddings generated | 0 |
| Skipped from cache | 3 |
| Failed chunks / batches | 0 / 0 |
| Batches submitted | 0 |
| Retry attempts | 0 (maximum configured: 3) |
| Estimated tokens | 0 |
| Approximate cost | `$0.00` |

The cache key combines the embedding model and exact chunk text. Successful batches are saved atomically; failures are counted and later batches continue. The automated tests also simulate a transient connection error followed by one exponential-backoff retry, and verify that an exhausted batch is reported while a later batch can still succeed.

The local token estimate is character-based (`ceil(characters / 4)`, minimum one per chunk), so real usage and provider pricing can differ. Set `--cost-per-million-tokens` to the relevant model rate for a better estimate, or supply a tokenizer counter when calling `run_batch_embedding()` from Python.