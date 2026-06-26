"""Règles métier des deux enveloppes AVISIA + disposition du formulaire.

Plafond = 250 € sur le montant REMBOURSÉ :
  CE            : remboursé à 50 %  → engageable ≈ 500 €
  APPRENTISSAGE : remboursé à 100 % → engageable = 250 €

Le LLM choisit l'enveloppe à partir du `hint` ; le MCP applique le taux + le plafond.
"""

# Disposition commune des deux formulaires (onglet "Feuil1"). ⚙️ PLOMBERIE — ne pas toucher.
FORM = {
    "tab": "Feuil1",
    "nom_cell": "B10",
    "prenom_cell": "B11",
    "desc_col": "A",       # DESCRIPTIF DES FACTURES
    "amount_col": "B",     # MONTANT ENGAGE
    "first_line_row": 15,
    "last_line_row": 28,
}

# ════════════════════════════════════════════════════════════════════════════════
# EXERCICE 1 — la règle de classement, en langage naturel
#
# Le `hint` est le SEUL texte que Claude lit pour décider dans quelle enveloppe ranger
# une facture. C'est de la logique métier pure : à toi de l'écrire.
#
# Le taux (rate) et le plafond (cap) sont déjà remplis — ce sont aussi des règles métier
# (250 € sur le remboursé), mais on les fige pour que rien ne plante.
#
# TODO 1 — remplace les `hint: ""` par une vraie consigne de classement :
#   • quels TYPES de dépenses vont dans cette enveloppe ?
#   • quelques MARCHANDS typiques (ça aide énormément Claude).
# ════════════════════════════════════════════════════════════════════════════════
ENVELOPES = {
    "CE": {
        "label": "Subvention CE",
        "reimbursement_rate": 0.5,   # 50 % (règle métier, ne pas toucher)
        "cap_reimbursed": 250.0,     # plafond sur le remboursé
        "currency": "EUR",
        "hint": "",  # TODO 1 — dépenses culturelles & sportives ? marchands ?
    },
    "APPRENTISSAGE": {
        "label": "Remboursement Apprentissage (Académie)",
        "reimbursement_rate": 1.0,   # 100 % (règle métier, ne pas toucher)
        "cap_reimbursed": 250.0,
        "currency": "EUR",
        "hint": "",  # TODO 1 — montée en compétences ? abonnements IA ? marchands ?
    },
}
