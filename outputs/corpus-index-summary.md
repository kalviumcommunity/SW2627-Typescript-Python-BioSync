# Corpus Vector Index Summary

Database: ChromaDB PersistentClient
Reachable: yes (heartbeat: 1791264110283397500)
Local path: `outputs/chroma`
Collection: `sprint_2_corpus_offline_fixture_v2`
Embedding model: `offline-fixture-v2`
Vector dimension: 8

## Count validation

Corpus chunks expected: 3
Prior ingestion summary chunks: 3
Current count matches prior ingestion summary: yes
Embeddings available: 3
Records upserted this run: 3
Indexed corpus records: 3
Count matches: yes
Stale corpus records removed: 0
Embedding cache skips: 0
Embedding failures: 0
Index failures: 0

## Spot-check readback

Matches source chunk: yes
ID: `8bfb92b5d644a001a16e93e8ca21c44b9be6c3f124a577bdb1f7db56edad2e7d`
Vector length: 8
Text: Customers can ask for a refund within thirty days.
Metadata: `{"chunk_index": 1, "model": "gpt-4o-mini", "overlap_tokens": 24, "position_end": 50, "position_start": 0, "record_type": "corpus_chunk", "section": "token-window", "source": "faq.html", "strategy": "token", "token_count": 10, "token_end": 10, "token_start": 0}`

The collection stores each embedding as a vector, original chunk text as the document, and source/chunk metadata as scalar fields. IDs are deterministic, so reruns update the same records; stale corpus-tagged IDs are removed only after all current chunks were embedded and upserted successfully.

## Failures

- None
