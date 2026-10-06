# Stored Chunk Embeddings

Source: offline fixture (no API request)

The committed report uses the reproducible offline fixture because this checkout has no API credentials. Run `python -m src.embedding_demo` with `API_BASE_URL`, `OPENAI_API_KEY`, and `EMBEDDING_MODEL` in `.env` to generate provider-backed vectors and store them with their source chunks.

Chunks embedded: 3
Vector length: 8
Every stored vector has the expected length: True

## Stored records

### Record 1

Text: annual plan refunds are available within thirty days
Metadata: `{'source': 'policy.txt', 'section': 'refunds', 'chunk_index': 1, 'page': 1}`
Vector length: 8
Vector sample: [0.9100, 0.1200, 0.2400, 0.0800, 0.0300, 0.1100, 0.1800, 0.0700, ...]

### Record 2

Text: customers can request a refund for an annual plan within 30 days
Metadata: `{'source': 'faq.html', 'section': 'refunds', 'chunk_index': 2, 'page': None}`
Vector length: 8
Vector sample: [0.8800, 0.1600, 0.2700, 0.1000, 0.0400, 0.1300, 0.1700, 0.0900, ...]

### Record 3

Text: the office cafeteria serves soup on Thursdays
Metadata: `{'source': 'onboarding.md', 'section': 'facilities', 'chunk_index': 1, 'page': None}`
Vector length: 8
Vector sample: [0.0500, 0.8200, 0.0900, 0.7100, 0.1800, 0.0300, 0.1200, 0.6600, ...]

## Retrieval note

Each vector remains attached to its original chunk text and metadata, so a similarity search can return the matching passage together with its source document, section, and chunk index.

# Similarity Ranking

Embedding source: offline fixture (no API request)
Query: Can I get a refund for my annual subscription within 30 days?
Metric: cosine similarity (higher scores indicate more aligned vector directions).

Cosine similarity compares vector direction rather than magnitude, making it a useful ranking score for text embeddings. It is a similarity, not a distance: higher is closer in meaning according to the embedding model. A high score is not proof that a chunk is correct or sufficient.

## Ranked chunks

### 1. Cosine similarity: 0.9994

Text: annual plan refunds are available within thirty days
Metadata: `{'source': 'policy.txt', 'section': 'refunds', 'chunk_index': 1, 'page': 1}`

### 2. Cosine similarity: 0.9993

Text: customers can request a refund for an annual plan within 30 days
Metadata: `{'source': 'faq.html', 'section': 'refunds', 'chunk_index': 2, 'page': None}`

### 3. Cosine similarity: 0.2615

Text: the office cafeteria serves soup on Thursdays
Metadata: `{'source': 'onboarding.md', 'section': 'facilities', 'chunk_index': 1, 'page': None}`

## Most similar

annual plan refunds are available within thirty days (score: 0.9994; source: policy.txt)

## Least similar

the office cafeteria serves soup on Thursdays (score: 0.2615; source: onboarding.md)

The highest-ranked chunk is the first retrieval candidate; the score orders candidates but does not independently verify their claims.
