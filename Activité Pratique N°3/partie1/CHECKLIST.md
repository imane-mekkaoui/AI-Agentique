# Checklist — RAG multimodal agentique

## Extraction et indexation

- [x] Choisir un PDF contenant du texte, des images et des tableaux.
- [x] Vérifier le PDF : 110 pages, texte et images détectés, 24 tableaux repérés.
- [x] Extraire le texte avec LlamaIndex.
- [x] Extraire les images et les enregistrer avec leurs métadonnées.
- [x] Extraire les tableaux et les convertir en texte structuré.
- [x] Créer des embeddings pour le texte et les tableaux.
- [x] Créer des embeddings d’images avec CLIP.
- [x] Stocker les vecteurs dans ChromaDB.
- [x] Tester la recherche de tableaux et d’images.
- [x] Générer et indexer des descriptions Qwen2-VL-2B pour les 25 images.

## RAG et agent

- [x] Connecter la recherche multimodale à Ollama depuis le notebook.
- [x] Générer une réponse à partir du contexte retrouvé, avec consigne de ne pas inventer.
- [x] Afficher les sources de chaque réponse : document, page, type et image si disponible.
- [x] Tester le RAG avec plusieurs questions et vérifier la qualité des réponses.
- [x] Créer un agent LangGraph qui choisit les recherches à effectuer : texte, image ou tableau.
- [x] Ajouter une recherche complémentaire lorsque les premiers résultats sont insuffisants.

## Interface et livraison

- [x] Ajouter une interface interactive ipywidgets au notebook pour poser des questions.
- [x] Afficher les réponses, les sources et les images pertinentes dans le notebook.
- [x] Ajouter des tests ciblés dans le notebook pour le routage, la recherche complémentaire, les citations et l’agent.
- [x] Valider plusieurs questions de bout en bout avec Ollama et vérifier la qualité des réponses.
- [ ] Ajouter Docker si nécessaire pour la démonstration ou le déploiement.
- [x] Rédiger les instructions d’installation et d’utilisation dans `README.md`.
