# lab_pytorch_v1

Lab PyTorch (vidéo Youssfi, Part 1).

**Dépôt GitHub :** [imane-mekkaoui/AI-Agentique](https://github.com/imane-mekkaoui/AI-Agentique)  
**Date de création du dépôt :** 24 novembre 2026

Le dossier `.venv` n’est **pas** versionné. Après un clone : `uv sync`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `lab1.ipynb` | Tenseurs, device CPU/CUDA, opérations (`+`, `*`, `@`), `requires_grad`, `backward`, `autograd` |
| `reg.ipynb` | Régression linéaire (`y = 3x + 2` + bruit), MLP séquentiel / classe `nn.Module`, classification CrossEntropy |
| `rapport.md` | Mini-rapport (étapes, résultats, points retenus) |

## Environnement

Python **3.11**, géré avec [uv](https://docs.astral.sh/uv/). Le virtualenv est **dans ce dossier** :

`tps/lab_pytorch_v1/.venv`

Commandes (déjà faites si `.venv` et `uv.lock` sont présents) :

```powershell
cd tps\lab_pytorch_v1
uv init --python 3.11
uv venv
uv add ipykernel torch numpy matplotlib torchmetrics
```

Pour réinstaller les dépendances :

```powershell
cd tps\lab_pytorch_v1
uv sync
```

## Noyau du notebook

Dans Cursor / VS Code : **Select Kernel** → **Select Another Kernel…** → **Jupyter Kernel** → `lab_pytorch_v1 (.venv)`.

Sinon, chemin direct :

`C:\Users\dell\Documents\projet_AIGenerative\tps\lab_pytorch_v1\.venv\Scripts\python.exe`

Ne pas utiliser Anaconda (`base`, `data_analyst`) ni le Python global.

## Dépendances

- `torch`
- `numpy`
- `matplotlib`
- `ipykernel`
- `torchmetrics` (R², matrice de confusion)
