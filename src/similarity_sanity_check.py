"""Check known relevance cases against the offline similarity ranking fixture."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.embedding_demo import (
    OFFLINE_QUERY_VECTOR,
    OFFLINE_VECTORS,
    SAMPLE_CHUNKS,
    rank_chunks,
    stored_embeddings_from_vectors,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
NEAR_TIE_THRESHOLD = 0.001


@dataclass(frozen=True)
class SanityCase:
    case_id: str
    query: str
    query_vector: tuple[float, ...]
    relevant_sources: tuple[str, ...]
    expected_top_source: str | None = None
    note: str = ""


SANITY_CASES = (
    SanityCase(
        case_id="refund-eligibility",
        query="Can I get a refund for my annual subscription within 30 days?",
        query_vector=OFFLINE_QUERY_VECTOR,
        relevant_sources=("policy.txt", "faq.html"),
        note="Both policy and FAQ passages answer refund eligibility.",
    ),
    SanityCase(
        case_id="office-facilities",
        query="What does the office cafeteria serve on Thursdays?",
        query_vector=OFFLINE_VECTORS[2],
        relevant_sources=("onboarding.md",),
        note="The onboarding facilities passage is the known relevant source.",
    ),
    SanityCase(
        case_id="refund-faq-wording",
        query="Can customers ask for a refund within thirty days?",
        query_vector=OFFLINE_QUERY_VECTOR,
        relevant_sources=("faq.html", "policy.txt"),
        expected_top_source="faq.html",
        note="The FAQ is the preferred source for this wording, but policy and FAQ are both relevant.",
    ),
)


def evaluate_cases(
    cases: Sequence[SanityCase] = SANITY_CASES,
) -> dict[str, object]:
    """Rank every case and check that relevant sources precede unrelated ones."""
    records = stored_embeddings_from_vectors(SAMPLE_CHUNKS, OFFLINE_VECTORS)
    results: list[dict[str, object]] = []
    for case in cases:
        ranked = rank_chunks(case.query_vector, records)
        sources = [record.metadata["source"] for _, record in ranked]
        relevant_positions = [index for index, source in enumerate(sources) if source in case.relevant_sources]
        unrelated_positions = [index for index, source in enumerate(sources) if source not in case.relevant_sources]
        passed = bool(relevant_positions) and (
            not unrelated_positions or min(relevant_positions) < min(unrelated_positions)
        )
        top_score, top_record = ranked[0]
        relevant_scores = [score for score, record in ranked if record.metadata["source"] in case.relevant_sources]
        unrelated_scores = [score for score, record in ranked if record.metadata["source"] not in case.relevant_sources]
        best_unrelated_score = max(unrelated_scores) if unrelated_scores else None
        preferred_score = next(
            (score for score, record in ranked if record.metadata["source"] == case.expected_top_source),
            None,
        )
        margin_to_preferred = (top_score - preferred_score) if preferred_score is not None else None
        surprising = (
            case.expected_top_source is not None
            and top_record.metadata["source"] != case.expected_top_source
            and margin_to_preferred is not None
            and margin_to_preferred <= NEAR_TIE_THRESHOLD
        )
        results.append(
            {
                "case_id": case.case_id,
                "query": case.query,
                "relevant_sources": list(case.relevant_sources),
                "ranked": [
                    {"rank": index, "source": record.metadata["source"], "score": score}
                    for index, (score, record) in enumerate(ranked, start=1)
                ],
                "top_source": top_record.metadata["source"],
                "top_score": top_score,
                "best_unrelated_score": best_unrelated_score,
                "relevant_above_unrelated": passed,
                "surprising": surprising,
                "preferred_source": case.expected_top_source,
                "preferred_source_score": preferred_score,
                "top_margin_over_preferred": margin_to_preferred,
                "note": case.note,
            }
        )

    pass_count = sum(bool(result["relevant_above_unrelated"]) for result in results)
    surprising_count = sum(bool(result["surprising"]) for result in results)
    return {
        "metric": "cosine similarity",
        "fixture": "deterministic 8-dimensional offline embeddings",
        "test_count": len(results),
        "passes": pass_count,
        "failures": len(results) - pass_count,
        "surprising_cases": surprising_count,
        "results": results,
    }


def render_report(report: dict[str, object]) -> str:
    """Render scores, pass/fail counts, and the discovered near-tie for review."""
    results = report["results"]
    lines = [
        "# Similarity Sanity Report",
        "",
        f"Metric: {report['metric']}",
        f"Fixture: {report['fixture']}",
        f"Test cases: {report['test_count']}",
        f"Passes: {report['passes']}",
        f"Failures: {report['failures']}",
        f"Surprising / borderline cases: {report['surprising_cases']}",
        "",
        "A case passes when at least one labeled relevant source ranks above every unrelated source. A preferred source is advisory when multiple passages are relevant.",
        "",
        "## Cases",
        "",
    ]
    for result in results:
        status = "PASS" if result["relevant_above_unrelated"] else "FAIL"
        if result["surprising"]:
            status += " (borderline preferred-source order)"
        lines.extend(
            [
                f"### {result['case_id']}: {status}",
                "",
                f"Query: {result['query']}",
                f"Known relevant sources: {', '.join(result['relevant_sources'])}",
                f"Top-ranked source: {result['top_source']} ({result['top_score']:.6f})",
            ]
        )
        if result["best_unrelated_score"] is not None:
            lines.append(f"Best unrelated score: {result['best_unrelated_score']:.6f}")
        ranking = ", ".join(
            f"{item['rank']}. {item['source']} ({item['score']:.6f})"
            for item in result["ranked"]
        )
        lines.extend([f"Ranking: {ranking}", f"Note: {result['note']}", ""])
    borderline = next((result for result in results if result["surprising"]), None)
    if borderline:
        lines.extend(
            [
                "## What the surprising case revealed",
                "",
                f"For `{borderline['case_id']}`, the preferred source `{borderline['preferred_source']}` scored {borderline['preferred_source_score']:.6f}, while `{borderline['top_source']}` ranked first at {borderline['top_score']:.6f}. The margin is only {borderline['top_margin_over_preferred']:.6f}, below the {NEAR_TIE_THRESHOLD:.3f} near-tie threshold. Both passages are labeled relevant, so this is not a relevance failure; it shows that this small fixture cannot reliably choose a canonical citation between two near-duplicate refund sources.",
                "",
                "## Scope",
                "",
                "These deterministic vectors check ranking logic and known labels, not the quality of a live embedding model. Both refund prompts intentionally reuse the same synthetic query vector, so the near-tie does not show how an embedding model distinguishes their wording. Mismatched embedding models or dimensions invalidate vector comparisons. Broader retrieval evaluation should use a larger labeled query set and metrics such as Recall@k, MRR, or nDCG.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "similarity-sanity-report.md",
    )
    args = parser.parse_args()
    report = evaluate_cases()
    rendered = render_report(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())