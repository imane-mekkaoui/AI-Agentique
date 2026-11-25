"""Construit ~1000 paires query/passage pour adapter le reranker (L2.3)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tests.make_fixtures import generate  # noqa: E402

from maintidoc.ingestion.chunking import passages_from_pages  # noqa: E402
from maintidoc.ingestion.pdf_extract import extract_pages  # noqa: E402
from maintidoc.models import AccessLevel, DocumentRecord  # noqa: E402

TEMPLATES = [
    "Que signifie {hint} ?",
    "Procédure liée à : {hint}",
    "Quelle valeur pour {hint} ?",
    "Photo : {hint} — que dit le manuel ?",
    "How do I check {hint}?",
]

OUT = _ROOT / "data" / "rerank" / "pairs.jsonl"


def _hint(text: str) -> str:
    words = text.split()
    if len(words) < 6:
        return text[:80]
    start = 0 if len(words) < 12 else 2
    return " ".join(words[start : start + 8])


def main() -> None:
    random.seed(2)
    fixture_dir = _ROOT / "tests" / "fixtures"
    generate(fixture_dir)
    pdfs = sorted(fixture_dir.glob("*.pdf"))
    chunks: list[str] = []
    for i, pdf in enumerate(pdfs):
        record = DocumentRecord(
            document_id=f"FIX-{i:03d}",
            title=pdf.stem,
            version="1",
            equipment_family="pompes",
            access_level=AccessLevel.PUBLIC,
            filename=pdf.name,
        )
        pages = extract_pages(pdf)
        passages = passages_from_pages(
            record, [(p.page, p.text) for p in pages], 40, 8
        )
        chunks.extend(p.text for p in passages if len(p.text) > 40)
    if len(chunks) < 4:
        chunks.extend(
            [
                "Pression maximale du sécheur SD-100 : 8 bar.",
                "Alignement d'accouplement : règle et jauge d'épaisseur.",
                "Voyant orange clignotant : défaut non critique, consulter le panneau.",
                "Code superviseur SUPER-LOCK-40 : accès restreint.",
            ]
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with OUT.open("w", encoding="utf-8") as handle:
        while rows < 1000:
            pos = random.choice(chunks)
            neg = random.choice(chunks)
            if neg == pos:
                continue
            query = random.choice(TEMPLATES).format(hint=_hint(pos))
            handle.write(json.dumps({"query": query, "passage": pos, "label": 1}, ensure_ascii=False) + "\n")
            handle.write(json.dumps({"query": query, "passage": neg, "label": 0}, ensure_ascii=False) + "\n")
            rows += 2
    print(f"Écrit {rows} paires -> {OUT}")


if __name__ == "__main__":
    main()
