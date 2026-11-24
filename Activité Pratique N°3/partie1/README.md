# RAG multimodal agentique

Projet de démonstration d'un RAG sur un manuel PDF : extraction du texte, des
images et des tableaux, indexation dans ChromaDB, puis recherche multimodale
et génération de réponses sourcées avec LangGraph et Ollama.

## Prérequis

- Windows 10/11 (les commandes ci-dessous sont pour PowerShell).
- Python 3.13 ou supérieur.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) pour installer
  les dépendances définies dans `pyproject.toml` et `uv.lock`.
- [Ollama](https://ollama.com/download) pour générer les réponses.
- Une connexion Internet lors de la première installation et du premier
  téléchargement des modèles Hugging Face.
- De l'espace disque et de la mémoire suffisants pour PyTorch, CLIP et
  Qwen2-VL-2B. Le notebook charge Qwen2-VL-2B sur CPU pour décrire les images;
  cette étape peut prendre du temps.

## Installation

Depuis la racine du projet, qui contient `pyproject.toml` :

```powershell
uv sync --group dev
```

Cette commande crée l'environnement `.venv` et installe les dépendances ainsi
que le noyau Jupyter (`ipykernel`). Dans VS Code, ouvrez le dossier racine
`projet_AIGenerative` (celui qui contient `pyproject.toml`), ouvrez le notebook
dans `partie1/`, puis sélectionnez l'interpréteur Python de `.venv` comme noyau.
Gardez le dossier racine du projet comme dossier de travail du noyau : les
notebooks utilisent des chemins relatifs vers `data/` et `chroma_db/`.

Installez et démarrez Ollama, puis récupérez un modèle de conversation :

```powershell
ollama pull qwen2.5:3b
ollama list
```

L'API Ollama doit être accessible à `http://127.0.0.1:11434`. L'application
Ollama la démarre habituellement automatiquement. Si elle ne tourne pas,
lancez `ollama serve` dans un terminal séparé. Pour vérifier l'API :

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Le nom saisi ensuite dans le notebook doit correspondre exactement à un nom
retourné par `ollama list`. Qwen2-VL-2B est un modèle Transformers utilisé pour
décrire les images; il est distinct du modèle de conversation Ollama.

## Préparer l'index

Le manuel d'exemple est `data/Manuale_ESSICCATOIO_FR.pdf`. Le notebook
`partie1/exploration.ipynb` extrait les contenus et crée les collections persistantes
dans `chroma_db/`. Il faut donc exécuter ses cellules dans l'ordre avant
d'interroger un index neuf :

1. Vérifier le PDF et son chemin.
2. Extraire le texte, les images et les tableaux.
3. Créer les embeddings et les collections Chroma.
4. Générer et indexer les descriptions d'images Qwen2-VL-2B.

Le premier téléchargement des modèles Hugging Face nécessite Internet.
Certaines cellules de `partie1/rag_agent.ipynb` utilisent `local_files_only=True` :
elles s'attendent donc à ce que les modèles soient déjà présents dans le cache
local. L'étape de description des images peut durer longtemps sur CPU; elle
n'est pas nécessaire à chaque lancement si les descriptions et les index sont
déjà créés.

Les résultats sont conservés dans `chroma_db/` et les images extraites dans
`data/images_extraites/`. Ne supprimez pas ces dossiers si vous souhaitez
réutiliser l'index existant. Si le PDF ou l'index manque, exécutez
`partie1/exploration.ipynb` avant `partie1/rag_agent.ipynb`.

## Poser des questions

1. Ouvrez `partie1/rag_agent.ipynb` dans VS Code et choisissez le noyau `.venv`.
2. Exécutez les cellules dans l'ordre. La première cellule de code reconnecte
   les collections Chroma et charge les embeddings de texte et CLIP.
3. Exécutez la cellule d'implémentation et, si souhaité, la cellule de tests
   fonctionnels simulés.
4. Dans le widget, entrez le nom d'un modèle Ollama installé, par exemple
   `qwen2.5:3b`, puis une question sur le manuel et cliquez sur
   **Rechercher et répondre**.
5. Le widget indique la recherche, le nombre de sources retenues et la
   génération. La réponse est suivie des citations (document, page, type,
   distance et extrait); une image est affichée si le chemin correspondant
   existe.

Une cellule de validation de bout en bout avec plusieurs questions et Ollama
est également incluse dans `partie1/rag_agent.ipynb`. Exécutez-la manuellement pour
vérifier les réponses et leurs sources avec le modèle réellement installé. Les
tests fonctionnels simulés ne sollicitent pas Ollama et ne remplacent pas cette
validation.

## Lancer l'API backend (partie 2)

Le notebook `partie2/backend_api.ipynb` teste les routes sans appeler Ollama.
Le code serveur est dans `partie2/api.py` et le runtime RAG partagé avec
`partie1/rag_agent.ipynb` dans `partie2/rag_runtime.py`.

Après avoir synchronisé les dépendances depuis la racine (`uv sync --group dev`),
assurez-vous que l'index existe et qu'Ollama est démarré. Dans PowerShell :

```powershell
$env:OLLAMA_MODEL = "qwen2.5:3b"
$env:RAG_CORS_ORIGINS = "http://localhost:5173"
uv run uvicorn partie2.api:app --host 127.0.0.1 --port 8000
```

Le nom du modèle doit correspondre à `ollama list`. L'API charge les collections
existantes de `chroma_db/` et les modèles de recherche une seule fois au démarrage.
`GET http://127.0.0.1:8000/health` vérifie l'état du service. Envoyez une question
en JSON à `POST http://127.0.0.1:8000/api/chat`, par exemple
`{"question": "Quelle est la plage de température ambiante ?"}`. La réponse
contient le texte généré et les sources (document, page, type, extrait et
distance). Les chemins d'images sont renvoyés comme métadonnées locales, pas
comme URLs servies par l'API.

## Dépannage

- **`WinError 10061` / connexion refusée** : vérifiez que l'application Ollama
  tourne et que `http://127.0.0.1:11434/api/tags` répond.
- **Modèle introuvable (404)** : exécutez `ollama list`, récupérez si besoin le
  modèle avec `ollama pull qwen2.5:3b`, puis saisissez son nom exact.
- **Collection Chroma introuvable** : vérifiez que `chroma_db/` existe à la
  racine du projet et exécutez `partie1/exploration.ipynb`.
- **Modèle Hugging Face introuvable localement** : assurez-vous que les étapes
  de préparation ont téléchargé le modèle dans le cache local; les cellules
  RAG ne le téléchargent pas.
- **Réponse sans source ou non concluante** : examinez les pages et extraits
  affichés. Le modèle doit répondre à partir de ces sources seulement; reformulez
  la question si les passages récupérés ne couvrent pas le sujet.

## Fichiers principaux

- `partie1/exploration.ipynb` : extraction, indexation et vérification des recherches.
- `partie1/rag_agent.ipynb` : RAG multimodal, agent LangGraph, tests et interface.
- `data/Manuale_ESSICCATOIO_FR.pdf` : document PDF d'exemple.
- `chroma_db/` : collections vectorielles persistantes produites par le projet.
