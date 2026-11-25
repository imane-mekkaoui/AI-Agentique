# L2.5 — Rapport comparatif reranker

Mesures à produire **après** `build_rerank_dataset.py` puis `eval_rerank.py`.
Les chiffres ci-dessous sont le protocole, pas une garantie.

| Configuration | nDCG@5 | MRR@10 |
| --- | --- | --- |
| sans reranker (`off`) | voir `docs/metrics_etape2.json` | idem |
| reranker initial (`base`) | mMARCO MiniLM | |
| reranker adapté (`adapted`) | 1 époque sur ~1000 paires fixtures | |

```powershell
cd projet
uv run python scripts/build_rerank_dataset.py
uv run python scripts/eval_rerank.py
# optionnel, CPU ~ quelques minutes
uv run python scripts/train_reranker.py
$env:RERANKER_MODE = "adapted"
uv run python scripts/eval_rerank.py
```

Limites : le jeu d’adaptation est synthétique (templates + fixtures), pas 800–1500 paires métier annotées à la main. À remplacer plus tard par des questions technicien vérifiées.
