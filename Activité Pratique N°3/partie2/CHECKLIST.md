# Checklist — Partie 2 : API et interface React

## Objectif

Réutiliser le RAG multimodal et l’agent LangGraph de `partie1/` dans une
application accessible par API, puis créer une interface React qui affiche les
réponses et leurs sources.

Les données, `chroma_db/` et l’environnement Python restent à la racine du
projet. Lancer les commandes depuis `projet_AIGenerative/`.

## 1. Vérifier les prérequis de la partie 1

- [x] Confirmer que l’index Chroma persistant et les notebooks de la partie 1
  existent.
- [x] Confirmer que l’agent LangGraph et le widget de questions sont présents
  dans `partie1/rag_agent.ipynb`.
- [x] Exécuter plusieurs questions réelles avec Ollama et vérifier que chaque
  réponse est étayée par ses citations.
- [x] Vérifier les réponses aux questions texte, tableau et image, puis noter
  les éventuels cas d’échec avant d’exposer le RAG par API.

## 2. Préparer le backend API

- [x] Choisir FastAPI comme framework Python de l’API.
- [x] Extraire le code réutilisable du RAG vers `partie2/rag_runtime.py`; les
  notebooks et l’API utilisent le même runtime et les collections Chroma
  persistantes.
- [x] Charger les modèles, les collections Chroma et l’agent une fois au
  démarrage du service.
- [x] Définir les schémas de requête et de réponse : question, réponse, citations
  et métadonnées des sources.
- [x] Ajouter `GET /health` et `POST /api/chat`.
- [x] Retourner les erreurs de validation en 422, les problèmes du service RAG
  en 502 et les erreurs d’initialisation dans les journaux du serveur.
- [x] Configurer les origines CORS via `RAG_CORS_ORIGINS`.

## 3. Tester le backend

- [x] Tester les schémas et les routes sans appeler Ollama avec un agent simulé
  dans `partie2/backend_api.ipynb`.
- [x] Tester le cas où aucune source pertinente n’est trouvée.
- [x] Tester le format et la présence des citations dans la réponse API.
- [x] Tester des requêtes réelles avec Ollama et vérifier les sources :
  température ambiante (page 60) et maintenance à 30 jours (page 83).
  La réponse de maintenance est construite depuis le tableau structuré et cite
  les opérations « graisser les supports » et « contrôler la tension des
  chaînes ».
- [x] Le service se connecte aux collections existantes de `chroma_db/` sans
  relancer l’extraction ni l’indexation.

## 4. Créer l’interface React

- [x] Choisir et initialiser Vite avec React et TypeScript dans
  `partie2/frontend/`.
- [x] Ajouter une zone de saisie, des suggestions et un bouton d’envoi.
- [x] Afficher la progression, la réponse Markdown et les erreurs réseau/API.
- [x] Afficher les sources avec document, page, type et extrait.
- [x] Afficher les images pertinentes lorsque l’API fournit un chemin ou une URL
  accessible.
- [x] Afficher les tableaux ou extraits structurés de façon lisible.
- [x] Permettre de poser plusieurs questions sans recharger la page.

## 5. Intégrer et livrer

- [x] Connecter React à l’API et configurer l’URL de l’API avec
  `VITE_API_URL`.
- [ ] Valider un parcours complet navigateur → API → RAG → Ollama → sources.
- [x] Documenter l’installation et le démarrage du backend et du frontend dans
  le README principal.
- [x] Docker n’est pas nécessaire pour la démonstration locale; les étapes de
  lancement du backend, d’Ollama et du frontend sont documentées séparément.
- [x] Mettre à jour le README principal avec les commandes de lancement.
