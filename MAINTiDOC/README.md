# MAINTiDOC — étape 2 (texte + photographie)

Assistant documentaire pour techniciens de maintenance. Les réponses sont
sourcées. Aucun diagnostic garanti, aucun pilotage de machine.

## Prérequis

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker (Qdrant)
- Optionnel : [Ollama](https://ollama.com) (`ollama pull qwen2.5:3b`)
- Optionnel : Tesseract OCR pour les pages scannées

## Installation

```powershell
cd projet
Copy-Item .env.example .env
uv sync --extra dev
```

## Démarrer Qdrant

```powershell
docker compose up -d
```

## Fixtures PDF de démonstration

Le corpus métier (30–50 PDF) sera ajouté plus tard dans `data/corpus/` et
déclaré dans `data/catalog.yaml`. Pour l’instant :

```powershell
uv run python tests/make_fixtures.py
```

## Indexation

```powershell
uv run python scripts/ingest.py
```

Le premier lancement télécharge BGE-M3.

## API

```powershell
uv run uvicorn maintidoc.api.app:app --app-dir src --host 127.0.0.1 --port 8000
```

Exemple :

```powershell
uv run python -c "import httpx; print(httpx.post('http://127.0.0.1:8000/ask', json={'question':'Quelle pression max pour le secheur SD-100 ?','user_id':'u1','role':'technicien'}).json())"
```

## Interface Streamlit

```powershell
$env:MAINTIDOC_API_URL = "http://127.0.0.1:8000"
uv run streamlit run src/maintidoc/ui/streamlit_app.py
```

Choisir un rôle (`operateur` / `technicien` / `superviseur`). On peut joindre une **photo** (voyant, panneau).

Option VLM : `ollama pull qwen2.5vl:3b` (sinon légende CLIP).

Reranker (nDCG@5 / MRR@10) : voir `docs/etape2.md`.

## Étape 3 — GMAO MCP + HITL

```powershell
uv run python -m maintidoc.mcp_server
```

Dans Streamlit, onglet **Ticket GMAO** : Consulter GMAO → **Approuver** (technicien) ou lecture seule (opérateur). Détail : `docs/etape3.md`.

Redémarrer l’API après mise à jour du code.

## Tests

```powershell
uv run pytest -q
```

## Checklist de validation

- [ ] Qdrant répond sur `http://127.0.0.1:6333`
- [ ] `scripts/ingest.py` indexe les fixtures sans erreur
- [ ] Une question sur le sécheur SD-100 donne une réponse + citation (document, version, page)
- [ ] Un `operateur` qui demande le code vanne CP-40 obtient « Je ne sais pas » sans citation superviseur
- [ ] Une question hors corpus (gâteau, météo) donne « Je ne sais pas »
- [ ] Streamlit affiche la réponse et les sources
- [ ] Aucun secret dans `.env.example` ; `.env` non versionné
- [ ] `uv run pytest -q` est vert
