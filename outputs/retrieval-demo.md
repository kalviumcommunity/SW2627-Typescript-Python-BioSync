# Top-k Retrieval Sample

Query: Can I get a refund for an annual plan within 30 days?
Embedding model: `offline-fixture-v2` (same model recorded on the document collection)
Query vector dimension: 8
Search: Chroma cosine distance converted to similarity score (`1 - distance`; higher is more similar).

## Results by k

### k = 1

1. Score: 0.999438 | Source: `policy.txt` | Chunk: `1`
   ID: `e68f70657a9fb6124de103c8069edabb36c03414d6d1711ee26ddcff5bab29fd`
   Text: Acme support policy

Annual plans can be refunded within 30 days. Refunds ' return to the original payment method.
   Metadata: `{"chunk_index": 1, "model": "gpt-4o-mini", "overlap_tokens": 24, "position_end": 114, "position_start": 0, "record_type": "corpus_chunk", "section": "token-window", "source": "policy.txt", "strategy": "token", "token_count": 25, "token_end": 25, "token_start": 0}`

### k = 3

1. Score: 0.999438 | Source: `policy.txt` | Chunk: `1`
   ID: `e68f70657a9fb6124de103c8069edabb36c03414d6d1711ee26ddcff5bab29fd`
   Text: Acme support policy

Annual plans can be refunded within 30 days. Refunds ' return to the original payment method.
   Metadata: `{"chunk_index": 1, "model": "gpt-4o-mini", "overlap_tokens": 24, "position_end": 114, "position_start": 0, "record_type": "corpus_chunk", "section": "token-window", "source": "policy.txt", "strategy": "token", "token_count": 25, "token_end": 25, "token_start": 0}`

2. Score: 0.999314 | Source: `faq.html` | Chunk: `1`
   ID: `8bfb92b5d644a001a16e93e8ca21c44b9be6c3f124a577bdb1f7db56edad2e7d`
   Text: Customers can ask for a refund within thirty days.
   Metadata: `{"chunk_index": 1, "model": "gpt-4o-mini", "overlap_tokens": 24, "position_end": 50, "position_start": 0, "record_type": "corpus_chunk", "section": "token-window", "source": "faq.html", "strategy": "token", "token_count": 10, "token_end": 10, "token_start": 0}`

3. Score: 0.261503 | Source: `onboarding.md` | Chunk: `1`
   ID: `0f97a5fb1b847b23fa35ee08e985faaf9bcb8c403b077653b314646d8536e25a`
   Text: # Support onboarding

Use the account email to locate a customer record.

Escalate payment disputes to the billing team.
   Metadata: `{"chunk_index": 1, "model": "gpt-4o-mini", "overlap_tokens": 24, "position_end": 120, "position_start": 0, "record_type": "corpus_chunk", "section": "token-window", "source": "onboarding.md", "strategy": "token", "token_count": 24, "token_end": 24, "token_start": 0}`

## Changing k

Increasing k returns more ranked candidates for downstream grounding, at the cost of more context to inspect and pass to generation. The same query vector is reused for each k so the result sets are directly comparable.
