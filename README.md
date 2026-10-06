# RAG Assistant Foundation

This repository contains the isolated foundation for an internal retrieval-augmented generation (RAG) assistant.

## Workspace

- `data/`: local knowledge-base documents. Contents are ignored by Git.
- `src/`: application and setup-check source code.
- `prompts/`: versioned prompt templates.
- `outputs/`: generated local results. Contents are ignored by Git.

## Document intake

Load the tracked sample corpus into source-tagged plain text:

```powershell
python -m src.document_loader
```

The loader supports TXT, Markdown, HTML, and PDF files. Each successful document prints its source filename, extracted character count, and a short sample. Missing, unreadable, empty, and unsupported files are reported and skipped so one bad input does not stop the corpus run. PDF extraction uses `pypdf`; other formats use the Python standard library. The sample corpus is in `data/sample-corpus/`.

Every loaded document passes through the same `clean_text()` function. It applies Unicode NFKC normalization, repairs common encoding artifacts, removes page markers and repeated short header/footer lines, and collapses whitespace. The CLI prints before/after samples; committed evidence is in `docs/cleaning-sample-output.md`.

## Chunking comparison

Compare paragraph chunks with fixed 80-character chunks and 20-character overlap on the cleaned sample corpus:

```powershell
python -m src.chunking
```

The comparison reports chunk counts, average character sizes, source IDs, and sample boundaries. Paragraph chunking is selected for this corpus because policy, onboarding, and FAQ content is naturally organized into short semantic sections. See `docs/chunking-comparison.md` for the sample output and rationale.

Every chunk now carries the same metadata fields: `source`, `section`, `page`, `position_start`, `position_end`, `chunk_index`, and `strategy`. `trace_chunk()` verifies the recorded span against the cleaned source text, providing a direct citation path. Metadata examples and traceback evidence are in `docs/chunk-metadata-samples.md`.

## Token-aware chunking

Run the tokenizer-backed chunker with `tiktoken`:

```powershell
python -m src.token_chunking
```

The default is 128 tokens with a controlled 24-token overlap using the `gpt-4o-mini` tokenizer. The limit is deliberately below a typical chat context window so retrieved chunks leave room for the system prompt, question, and answer. The overlap is about 19% of a chunk: enough to preserve short ideas across boundaries without paying the duplication cost of a much larger overlap. See `docs/token-chunking-sample-output.md` for counts, sample chunks, and the boundary demonstration.

## Full-corpus ingestion

Run the complete pipeline over every file under `data/`:

```powershell
python -m src.ingestion_pipeline
```

The run discovers all files recursively, loads and cleans supported documents, token-chunks every successful document, records unsupported or unreadable files as failures, and asserts `total sources = successfully ingested + failures`. The committed report is `docs/full-ingestion-summary.json` and includes counts, failures, and sample chunks with metadata.

## Reusable prompt templates

The grounded prompt template lives in `prompts/templates.py`, separate from application logic. Its named `{context}` and `{question}` placeholders are filled at runtime by both `src.chat_completion` and `src.parameter_experiments`, keeping the chat and batch paths consistent. Example filled prompts are in `docs/prompt-template-renders.md`.

## Setup

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the pinned dependency ranges:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Create local configuration from the template and add values locally:

   ```powershell
   Copy-Item .env.example .env
   ```

   `.env` must contain `API_BASE_URL`, `OPENAI_API_KEY`, `CHAT_MODEL`, and `EMBEDDING_MODEL`. It is ignored by Git and must never be committed.

5. Run the setup check:

   ```powershell
   python -m src.check_setup
   ```

The check loads local configuration without making an API request. A fresh setup was verified successfully after installing `requirements.txt`; with the blank example values it reports only that optional API configuration still needs to be filled in.

## First chat completion

After filling in `API_BASE_URL`, `OPENAI_API_KEY`, and `CHAT_MODEL` in `.env`, run:

```powershell
python -m src.chat_completion
```

The script sends one system message and one user message, prints `choices[0].message.content`, and logs the request messages, response payload, and token usage when available. Logs are written to `outputs/chat_exchange.log`, which is ignored by Git. Authentication failures (401), rate limits (429), connection errors, and other API errors are reported without a raw stack trace. See `docs/sample-chat-output.md` for redacted sample output.

## Parameter experiments

Run the same grounded prompt with different generation controls:

```powershell
python -m src.parameter_experiments
```

The command runs temperature, `max_tokens`, and `top_p` comparisons and writes the captured responses and token usage to `outputs/parameter-experiments.md` and `outputs/parameter-experiments.json`. Recommended settings for factual answers are documented in `docs/grounded-generation-settings.md`.

## Structured JSON responses

Run the structured-output client after filling in the API values in `.env`:

```powershell
python -m src.structured_output
```

The client requests JSON mode with `response_format`, parses the response into an `answer`/`source` dict, validates both required non-empty string fields, and reports malformed or incomplete output without an unhandled JSON exception. It retries without JSON mode when an older compatible endpoint rejects that option. Offline behavior is covered by `python -m unittest src.test_structured_output -v`; sample parsed results are in `outputs/structured-output-samples.md` and `outputs/structured-output-results.json`.

## Embedding demonstration

Generate embeddings for three sample chunks and a refund query, then rank the chunks by cosine similarity:

```powershell
python -m src.embedding_demo
```

The command uses `API_BASE_URL`, `OPENAI_API_KEY`, and `EMBEDDING_MODEL` from `.env` through the configured OpenAI-compatible API. It embeds the chunks and query, ranks chunks from highest to lowest cosine similarity, and prints each score with its source text and metadata. Cosine similarity compares vector direction, so larger values rank as more similar; unlike a distance, a larger similarity score is better. A high score is a retrieval signal, not a guarantee that the chunk is correct or sufficient. Use `python -m src.embedding_demo --offline-fixture` to reproduce the committed sample ranking without an API request. The sample output is in `outputs/embedding-demo.md`.

## Batch embedding pipeline

Embed token chunks across the sample corpus in configurable batches, with retries for transient API failures and a local cache to avoid repeat requests:

```powershell
python -m src.batch_embedding --batch-size 64
```

The default cache is `outputs/embedding-cache.json`; it is local and ignored by Git. Cache entries are keyed by embedding model and exact chunk text. Successful batches are persisted atomically, while exhausted batches are counted and reported without stopping later batches. Retries use exponential backoff for connection/time-out errors and transient HTTP statuses (including rate limits). The run reports total chunks, generated embeddings, cache skips, failures, retry attempts, estimated tokens, and approximate cost. Cost is controlled by `--cost-per-million-tokens` (default `$0.02`); token counts use a local character-based estimate unless a tokenizer counter is supplied in code. Use `--offline-fixture` to exercise the pipeline without API credentials, and override `--cache`/`--summary` for isolated runs. `outputs/batch-embedding-summary.md` contains two reproducible offline runs, including the rerun that skips previously embedded chunks.

## Similarity sanity checks

Run deterministic known-relevance cases against the cosine ranker before trusting retrieval:

```powershell
python -m src.similarity_sanity_check
```

The evaluator checks whether a labeled relevant source ranks before unrelated sources, reports top sources and scores, and calls out close preferred-source ties without treating two relevant passages as a relevance failure. It uses the offline 8-dimensional fixture and does not validate the quality of a live embedding model. The committed result is `outputs/similarity-sanity-report.md`; tests include both the expected borderline case and a deliberately missing relevant-source label to verify failure reporting. For broader quality measurement, build a representative labeled query set and track Recall@k, MRR, or nDCG.

## Local vector store

Create a persistent local ChromaDB collection, embed a test source chunk, and verify it can be read back:

```powershell
python -m src.vector_store --offline-fixture
```

`VECTOR_DB_PATH` and `VECTOR_DB_COLLECTION` in `.env` select the local database directory and live collection; the defaults are `outputs/chroma` and `sprint_2_chunks`. The offline command uses a separate `VECTOR_DB_OFFLINE_COLLECTION` by default so its fixture vectors cannot contaminate a live model collection. The script reports Chroma heartbeat reachability, creates a cosine collection whose dimension is taken from the inserted vector, and checks stored model/dimension metadata on reuse. Records store the vector as the embedding, source text as the document, and source/section/chunk/page fields as scalar metadata. Use the default API path after setting `API_BASE_URL`, `OPENAI_API_KEY`, and `EMBEDDING_MODEL` to create a vector in the configured model's actual dimension. The readback output is committed in `outputs/vector-db-readback.md`; local database files are ignored by Git.

## Corpus indexing

Embed, insert, and count-check every sample-corpus token chunk:

```powershell
python -m src.index_corpus --offline-fixture
```

The script reuses the embedding cache and Chroma configuration, uses stable IDs for repeatable upserts, removes stale corpus-tagged rows after a complete successful refresh, and checks the indexed count against both the current chunk set and `docs/full-ingestion-summary.json`. It reads a stored record back and compares its ID, text, metadata, and vector length to the source chunk. Live indexing uses the configured embedding API and `VECTOR_DB_COLLECTION`; fixture indexing uses a separate `VECTOR_DB_OFFLINE_INDEX_COLLECTION`. The committed run summary is `outputs/corpus-index-summary.md`.

## Top-k retrieval

Search the indexed collection with a query embedding from the same model, and compare different result counts:

```powershell
python -m src.retrieve_chunks --k 1 3
```

The live path uses `EMBEDDING_MODEL` to embed the query and rejects collection model or dimension mismatches. Chroma cosine distances are returned as similarity scores (`1 - distance`); each match includes its text, source metadata, chunk index, and stable ID. Search is filtered to `record_type=corpus_chunk` so setup probes do not appear as retrieved documents. Use `--offline-fixture` after running `python -m src.index_corpus --offline-fixture` to reproduce the sample without API credentials. The saved k comparison is in `outputs/retrieval-demo.md`.

## Reproducing the setup

Clone the repository, use the Python version above, follow the five setup steps, and keep real credentials only in the local `.env` file.
