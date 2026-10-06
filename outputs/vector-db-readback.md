# Vector Store Insert/Readback

Database: ChromaDB PersistentClient
Reachable: yes (heartbeat: 1791263129816038100)
Local path: `outputs/chroma`
Collection: `sprint_2_chunks_offline_fixture`
Distance metric: cosine
Embedding model: `offline-fixture-v1`
Collection dimension: 8

## Read-back record

ID: `vector-db-readback-test`
Vector length: 8
Text: Annual plans can be refunded within 30 days.
Metadata: `{"chunk_index": 1, "page": 1, "section": "refunds", "source": "policy.txt"}`
Vector sample: `[0.8999999165534973, 0.13999998569488525, 0.2549999952316284, 0.08999999612569809, 0.034999996423721313, 0.11999999731779099, 0.17499998211860657, 0.07999999821186066]`

The vector is stored as the collection embedding, the source text as its document, and citation fields as scalar metadata.
