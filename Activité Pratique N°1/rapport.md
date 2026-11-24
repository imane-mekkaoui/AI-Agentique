# Mini-rapport — lab PyTorch v1

**Cours :** Part 1 — Neural Network Fundamentals with PyTorch For Generative AI  
**Enseignant :** Prof. Mohamed Youssfi  
**Séance :** 12 octobre 2026  
**Dépôt :** https://github.com/imane-mekkaoui/AI-Agentique  
**Dossier :** `Activité Pratique N°1`

## Objectif

Reprendre la démonstration du cours : créer un projet `uv`, manipuler les tenseurs PyTorch, calculer un gradient, entraîner une régression linéaire, puis un MLP et un classifieur.

## Environnement

| Élément | Valeur |
|---|---|
| Outil | `uv` |
| Python | 3.11.14 |
| PyTorch | 2.15.0+cpu |
| GPU CUDA | non (`torch.cuda.is_available()` → `False`) |
| Device | CPU |
| Paquets | `torch`, `numpy`, `matplotlib`, `ipykernel`, `torchmetrics` |
| Noyau | `lab_pytorch_v1/.venv` |

## Travail réalisé

### 1. `lab1.ipynb` — tenseurs et gradient

- Import de `torch` / `numpy`, affichage de la version.
- Création de tenseurs (scalaire, vecteur, matrice), `zeros`, `dtype`, conversion `float32`, `randn`.
- `device` puis `.to(device)`.
- Opérations : somme `A + A`, produit terme à terme `A * A`, produit matriciel `A @ B`.
- Neurone `y = w x + b`, loss MSE `(y - 10)²`, `requires_grad=True`, `loss.backward()`.

**Résultats (comme au tableau) :**

| Exemple | y | loss | dL/dw | dL/db |
|---|---|---|---|---|
| x=2, w=3, b=1 | 7 | 9 | −12 | −6 |
| x=3, w=4, b=6 | 18 | 64 | 48 | 16 |

`torch.autograd.grad` donne les mêmes gradients (48 et 16) après un nouveau forward.

### 2. `reg.ipynb` — régression, MLP, classification

**Régression linéaire**

- Données : `linspace(-2, 2, 50)`, `unsqueeze(1)`, cible `y = 3x + 2` + bruit gaussien (`0.6 * randn_like`).
- Modèle : `nn.Linear(1, 1)`, `MSELoss`, Adam `lr=0.01`, 500 époques, `zero_grad` → forward → `backward` → `step`.
- Évaluation en `inference_mode`, métrique R² (`torchmetrics`).

MSE observée : ~19.6 (époque 0) → ~0.62 (époque 400).  
**R² ≈ 0.97.**

**MLP**

- Version `nn.Sequential` : 4 → 16 ReLU → 8 ReLU → 3.
- Même architecture dans une classe `MLP(nn.Module)` avec `forward`.

**Classification (2 classes)**

- 150 points par classe, 2 features.
- Réseau 2 → 16 ReLU → 16 ReLU → 2, `CrossEntropyLoss`, Adam, 200 époques.
- Loss : ~0.66 → ~0.0004.
- **Accuracy = 1.0** (données facilement séparables).
- Matrice de confusion : `[[150, 0], [0, 150]]`.

## Points retenus

1. Régression → `MSELoss` ; classification → `CrossEntropyLoss`.
2. Toujours `optimizer.zero_grad()` avant `backward`.
3. `model.train()` pour l’entraînement, `model.eval()` + `inference_mode` pour la prédiction.
4. `requires_grad=True` est obligatoire pour construire le graphe et calculer les gradients.

## Fichiers

- `lab1.ipynb` — bases PyTorch  
- `reg.ipynb` — régression + MLP + classification  
- `README.md` — installation et noyau  
- `pyproject.toml` / `uv.lock` — dépendances
