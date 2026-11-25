"""Adapte le cross-encoder sur data/rerank/pairs.jsonl (L2.4). CPU, 1 époque."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from sentence_transformers import InputExample, CrossEncoder
from torch.utils.data import DataLoader

from maintidoc.config import get_settings


def main() -> None:
    settings = get_settings()
    data_path = _ROOT / "data" / "rerank" / "pairs.jsonl"
    if not data_path.is_file():
        raise SystemExit("Lancer d'abord : uv run python scripts/build_rerank_dataset.py")
    examples = []
    with data_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            examples.append(
                InputExample(texts=[row["query"], row["passage"]], label=float(row["label"]))
            )
    model = CrossEncoder(settings.reranker_model, num_labels=1)
    loader = DataLoader(examples, shuffle=True, batch_size=8)
    out = Path(settings.reranker_adapted_path)
    out.mkdir(parents=True, exist_ok=True)
    model.fit(
        train_dataloader=loader,
        epochs=1,
        warmup_steps=10,
        show_progress_bar=True,
    )
    model.save(str(out))
    print(f"Reranker adapté -> {out}")


if __name__ == "__main__":
    main()
