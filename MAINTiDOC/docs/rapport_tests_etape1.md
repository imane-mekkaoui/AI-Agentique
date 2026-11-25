# L1.6 — Rapport de tests documentaires et d’accès

## Périmètre

Tests automatisés pytest, sans appel LLM ni Qdrant, sur les fixtures de `tests/fixtures/`
(générées à l’exécution).

## Cas couverts

| Test | Objectif | Résultat attendu |
| --- | --- | --- |
| `test_ingestion` | PyMuPDF extrait le texte page 1 | Texte SD-100 / 8 bar présent |
| `test_metadata` | Payload complet + deux familles | Champs exigés, `superviseur` sur FIX-CMP-002 |
| `test_access_filter` | Opérateur vs document superviseur | 0 citation, réponse « Je ne sais pas », secret absent |
| `test_citations` | Références vérifiables | document_id + version + page |
| `test_unknown_answer` | Contexte vide | « Je ne sais pas », LLM non appelé |

## Exécution

```powershell
cd projet
uv sync --extra dev
uv run pytest -q
```

## Limites

- Les tests d’intégration Qdrant / BGE-M3 / Ollama sont manuels (voir README).
- Le corpus métier 30–50 PDF n’est pas encore fourni ; les fixtures suffisent
  à valider le pipeline et le filtrage des droits.

## Critère de validation étape 1

Une question technique sur un passage public produit une réponse sourcée
(document + page). Un utilisateur `operateur` ne reçoit ni le code
`SUPER-LOCK-40` ni une citation vers le document superviseur.
