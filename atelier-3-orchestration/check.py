"""Pré-vol de l'atelier — lance `uv run python check.py` AVANT de commencer.

Contrairement aux ateliers 1 et 2, celui-ci touche à des outils EXTERNES (Docker, gcloud)
qui ne sont pas forcément installés en salle. Les checks Docker/gcloud sont donc INFORMATIFS
(⚠️, jamais bloquants) : sans eux tu peux quand même lire/coder tout le TODO métier — seuls
les exercices "build/run" nécessitent Docker, et l'étape cloud (exercice 4) est une démo
animateur, pas un exercice solo.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def check(label: str, cond: bool, hint: str = "") -> None:
    global ok
    mark = "✅" if cond else "❌"
    print(f"{mark} {label}" + ("" if cond else f"  → {hint}"))
    ok = ok and cond


def warn(label: str, cond: bool, hint: str = "") -> None:
    mark = "✅" if cond else "⚠️ "
    print(f"{mark} {label}" + ("" if cond else f"  → {hint}"))


# 1. dépendances Python
try:
    import mcp, starlette, uvicorn  # noqa: F401
    check("Dépendances Python (mcp, starlette, uvicorn)", True)
except Exception as e:  # noqa: BLE001
    check("Dépendances Python (mcp, starlette, uvicorn)", False, f"{e} — lance `uv sync`")

# 2. le MCP de l'atelier 1 — fourni TEL QUEL, à déployer (pas besoin de l'avoir SUIVI)
atelier1_dir = ROOT.parent / "atelier-1-serveur-mcp"
atelier1_server = atelier1_dir / "solution" / "server.py"
atelier1_templates = atelier1_dir / "templates"
atelier1_lock = atelier1_dir / "uv.lock"
check("MCP à déployer trouvé (atelier-1-serveur-mcp/solution/server.py)",
      atelier1_server.exists(),
      "atelier-1-serveur-mcp/ doit être présent à côté de ce dossier (mono-repo) — reclone "
      "le dépôt si besoin (aucun exercice de l'atelier 1 à faire, juste le fichier)")
check("Templates .xlsx de l'atelier 1 trouvés", atelier1_templates.is_dir(),
      f"introuvable : {atelier1_templates}")
check("uv.lock de l'atelier 1 trouvé (utilisé par le Dockerfile)", atelier1_lock.exists(),
      f"introuvable : {atelier1_lock} — lance `cd ../atelier-1-serveur-mcp && uv sync`")

# 3. fichiers du squelette de CET atelier
for rel in ("atelier/Dockerfile", "atelier/docker-compose.yml", "atelier/auth.py",
            "solution/Dockerfile", "solution/docker-compose.yml", "solution/auth.py"):
    check(f"{rel} présent", (ROOT / rel).exists(), "fichier manquant — reclone le dépôt")

# 4. Docker — SOFT check, jamais bloquant (pas tout le monde n'a Docker Desktop en salle)
docker_ok = shutil.which("docker") is not None
warn("Docker CLI disponible (`docker`)", docker_ok,
     "installe Docker Desktop pour faire les exercices 1-3 en autonomie — sinon suis-les "
     "en lecture, la démo des exercices 4-5 sera faite par l'animateur")

# 5. gcloud — SOFT check, jamais bloquant (l'étape 4 est une démo animateur, pas un exercice solo)
gcloud_ok = shutil.which("gcloud") is not None
warn("gcloud CLI disponible (`gcloud`)", gcloud_ok,
     "pas grave : le déploiement cloud (exercice 4) est fait EN DÉMO par l'animateur, tu "
     "n'as pas besoin de gcloud pour suivre")

print()
if ok:
    print("Tout est prêt côté fichiers/dépendances. Suis ATELIER.md pour démarrer.")
    if not docker_ok:
        print("ℹ️  Docker absent : tu peux lire/coder tout le TODO, juste pas builder l'image toi-même.")
    if not gcloud_ok:
        print("ℹ️  gcloud absent : pas un problème, l'étape cloud est une démo animateur.")
else:
    print("⚠️  Corrige les ❌ ci-dessus (fichiers/dépendances) avant de commencer.")
    sys.exit(1)
