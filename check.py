"""Pré-vol de l'atelier — lance `uv run python check.py` AVANT de commencer.

Vérifie que l'environnement est prêt (deps, templates), (re)crée 3 factures PDF de test
dans factures_a_classer/, et confirme que la solution de référence se charge. Aucun effet
de bord côté Claude — juste de quoi démarrer l'atelier sans galère d'installation.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def check(label: str, cond: bool, hint: str = "") -> None:
    global ok
    mark = "✅" if cond else "❌"
    print(f"{mark} {label}" + ("" if cond else f"  → {hint}"))
    ok = ok and cond


# 1. dépendances
try:
    import mcp, openpyxl, fitz  # noqa: F401
    check("Dépendances (mcp, openpyxl, pymupdf)", True)
except Exception as e:  # noqa: BLE001
    check("Dépendances (mcp, openpyxl, pymupdf)", False, f"{e} — lance `uv sync`")

# 2. templates .xlsx
tpl = ROOT / "templates"
check("Templates CE.xlsx + APPRENTISSAGE.xlsx",
      (tpl / "CE.xlsx").exists() and (tpl / "APPRENTISSAGE.xlsx").exists(),
      "templates/ manquant")

# 3. factures de test (créées si absentes)
inbox = ROOT / "factures_a_classer"
inbox.mkdir(exist_ok=True)
if not list(inbox.glob("*.pdf")):
    try:
        import fitz
        echantillons = {
            "ugc_cinema.pdf": "UGC Cine Cite\nFacture N 2026-04518\nDate: 14/06/2026\n"
                              "Place de cinema x2 - Seance VOST\nMontant TTC: 21,60 EUR",
            "openai_chatgpt.pdf": "OpenAI, LLC\nReceipt #2026-OA-77123\nDate: 01/06/2026\n"
                                  "ChatGPT Plus subscription (monthly)\nTotal: 22,00 EUR",
            "decathlon_sport.pdf": "DECATHLON Paris\nTicket 2026-IDF-9920\nDate: 09/06/2026\n"
                                   "Paire de chaussures running\nMontant TTC: 64,99 EUR",
        }
        for name, body in echantillons.items():
            d = fitz.open(); p = d.new_page(); p.insert_text((72, 90), body, fontsize=11)
            d.save(inbox / name); d.close()
    except Exception as e:  # noqa: BLE001
        check("Factures de test", False, str(e))
pdfs = sorted(f.name for f in inbox.glob("*.pdf"))
check(f"Factures de test dans factures_a_classer/ ({len(pdfs)})", bool(pdfs),
      "aucun PDF généré")

# 4. la solution de référence se charge
try:
    import asyncio
    sys.path.insert(0, str(ROOT / "solution"))
    import server as S  # noqa: E402
    n_tools = len(asyncio.run(S.mcp.list_tools()))
    check(f"solution/server.py se charge ({n_tools} tools)", n_tools == 5,
          f"{n_tools} tools au lieu de 5")
except Exception as e:  # noqa: BLE001
    check("solution/server.py se charge", False, str(e))

print()
if ok:
    print("Tout est prêt. Factures à classer :", ", ".join(pdfs))
    print("Démarre l'atelier :  ouvre atelier/server.py et suis ATELIER.md")
    print("Teste à tout moment :  uv run mcp dev atelier/server.py")
else:
    print("⚠️  Corrige les ❌ ci-dessus avant de commencer.")
    sys.exit(1)
