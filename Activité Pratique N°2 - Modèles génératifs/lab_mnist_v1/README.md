# lab_mnist_v1 — Activité pratique N°2


Le dossier `.venv` n’est **pas** versionné. Après un clone : `uv sync`.

## Environnement (Python 3.11, uv)

Dans ce dossier :

```powershell
uv init --python 3.11
uv venv
.\.venv\Scripts\Activate.ps1
uv add ipykernel torch torchvision matplotlib torcheval
```

Réinstaller :

```powershell
uv sync
```

Kernel Jupyter : **lab_mnist_v1** → `lab_mnist_v1/.venv/Scripts/python.exe` (pas Anaconda).

## Notebook

| Fichier | Contenu |
|---|---|
| `lab2.ipynb` | 1. MNIST  2. Classifieur  3. Auto-encodeur  4. VAE |

Époques volontairement petites (3 / 5) comme dans le cours, pour que ça tourne vite sur CPU.
