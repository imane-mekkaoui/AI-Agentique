"""Compare off / base / adapted : nDCG@5 et MRR@10 (L2.5)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from maintidoc.config import get_settings
from maintidoc.models import AccessLevel, Passage
from maintidoc.rag.rerank import mrr_at_k, ndcg_at_k, rerank


def _passage(text: str, i: int) -> Passage:
    return Passage(
        document_id=f"D{i}",
        title="eval",
        version="1",
        page=1,
        equipment_family="pompes",
        access_level=AccessLevel.PUBLIC,
        content_hash=f"{i:064d}"[:64],
        text=text,
    )


def main() -> None:
    settings = get_settings()
    data_path = _ROOT / "data" / "rerank" / "pairs.jsonl"
    if not data_path.is_file():
        raise SystemExit("Lancer d'abord scripts/build_rerank_dataset.py")
    by_query: dict[str, list[tuple[int, str]]] = defaultdict(list)
    with data_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            by_query[row["query"]].append((int(row["label"]), row["passage"]))
    queries = list(by_query.items())[:40]
    report: dict[str, dict[str, float]] = {}
    for mode in ("off", "base", "adapted"):
        ndcgs, mrrs = [], []
        for query, rows in queries:
            passages = [_passage(text, i) for i, (_, text) in enumerate(rows)]
            labels = {p.text: lab for lab, p in zip((r[0] for r in rows), passages)}
            if mode == "off":
                ordered = passages
            else:
                ordered = rerank(
                    query,
                    passages,
                    mode=mode,
                    base_model=settings.reranker_model,
                    adapted_path=settings.reranker_adapted_path,
                )
            rel = [labels.get(p.text, 0) for p in ordered]
            ndcgs.append(ndcg_at_k(rel, 5))
            mrrs.append(mrr_at_k(rel, 10))
        report[mode] = {
            "nDCG@5": round(sum(ndcgs) / len(ndcgs), 4),
            "MRR@10": round(sum(mrrs) / len(mrrs), 4),
        }
    out = _ROOT / "docs" / "metrics_etape2.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Écrit {out}")


if __name__ == "__main__":
    main()
