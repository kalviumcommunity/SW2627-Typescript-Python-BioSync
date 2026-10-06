# Similarity Sanity Report

Metric: cosine similarity
Fixture: deterministic 8-dimensional offline embeddings
Test cases: 3
Passes: 3
Failures: 0
Surprising / borderline cases: 1

A case passes when at least one labeled relevant source ranks above every unrelated source. A preferred source is advisory when multiple passages are relevant.

## Cases

### refund-eligibility: PASS

Query: Can I get a refund for my annual subscription within 30 days?
Known relevant sources: policy.txt, faq.html
Top-ranked source: policy.txt (0.999438)
Best unrelated score: 0.261503
Ranking: 1. policy.txt (0.999438), 2. faq.html (0.999314), 3. onboarding.md (0.261503)
Note: Both policy and FAQ passages answer refund eligibility.

### office-facilities: PASS

Query: What does the office cafeteria serve on Thursdays?
Known relevant sources: onboarding.md
Top-ranked source: onboarding.md (1.000000)
Best unrelated score: 0.288658
Ranking: 1. onboarding.md (1.000000), 2. faq.html (0.288658), 3. policy.txt (0.236352)
Note: The onboarding facilities passage is the known relevant source.

### refund-faq-wording: PASS (borderline preferred-source order)

Query: Can customers ask for a refund within thirty days?
Known relevant sources: faq.html, policy.txt
Top-ranked source: policy.txt (0.999438)
Best unrelated score: 0.261503
Ranking: 1. policy.txt (0.999438), 2. faq.html (0.999314), 3. onboarding.md (0.261503)
Note: The FAQ is the preferred source for this wording, but policy and FAQ are both relevant.

## What the surprising case revealed

For `refund-faq-wording`, the preferred source `faq.html` scored 0.999314, while `policy.txt` ranked first at 0.999438. The margin is only 0.000124, below the 0.001 near-tie threshold. Both passages are labeled relevant, so this is not a relevance failure; it shows that this small fixture cannot reliably choose a canonical citation between two near-duplicate refund sources.

## Scope

These deterministic vectors check ranking logic and known labels, not the quality of a live embedding model. Both refund prompts intentionally reuse the same synthetic query vector, so the near-tie does not show how an embedding model distinguishes their wording. Mismatched embedding models or dimensions invalidate vector comparisons. Broader retrieval evaluation should use a larger labeled query set and metrics such as Recall@k, MRR, or nDCG.
