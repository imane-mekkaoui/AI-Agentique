# Étape 2 — Multimodalité et reranker

Sans MCP, sans tickets (étape 3). Le RAG texte de l’étape 1 reste.

## Flux photo

```
photo + question
  → VLM (qwen2.5vl:3b) ou CLIP
  → recherche BGE (texte) + CLIP (figures)
  → fusion
  → reranker (off | base | adapted)
  → Qwen texte, citations, incertitude
```

## Livrables

| Réf. | Fichiers |
| --- | --- |
| L2.1 | `src/maintidoc/rag/vlm.py` |
| L2.2 | retriever fusion CLIP + Streamlit photo |
| L2.3 | `scripts/build_rerank_dataset.py` → `data/rerank/pairs.jsonl` |
| L2.4 | `scripts/train_reranker.py` → `models/reranker-adapted/` |
| L2.5 | `scripts/eval_rerank.py` (nDCG@5, MRR@10) |
| L2.6 | Streamlit + `POST /ask` avec `photo_b64` |

Qwen2.5-VL-7B est trop lourd ici : **qwen2.5vl:3b** via Ollama. Si le modèle n’est pas tiré, repli CLIP.
