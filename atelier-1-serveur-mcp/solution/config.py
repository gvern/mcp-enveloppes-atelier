"""Règles métier des deux enveloppes AVISIA + disposition du formulaire.

Plafond = 250 € sur le montant REMBOURSÉ (pris en charge).
  CE            : remboursé à 50 %  → engageable ≈ 500 €
  APPRENTISSAGE : remboursé à 100 % → engageable = 250 €

Le LLM choisit l'enveloppe à partir du `hint` ; le MCP applique seulement le taux + le
plafond.
"""

# Disposition commune des deux formulaires (onglet "Feuil1"). ⚙️ PLOMBERIE.
FORM = {
    "tab": "Feuil1",
    "nom_cell": "B10",
    "prenom_cell": "B11",
    "desc_col": "A",       # DESCRIPTIF DES FACTURES
    "amount_col": "B",     # MONTANT ENGAGE
    "first_line_row": 15,  # première ligne de facture
    "last_line_row": 28,   # dernière ligne (14 lignes max)
}

ENVELOPES = {
    "CE": {
        "label": "Subvention CE",
        "reimbursement_rate": 0.5,
        "cap_reimbursed": 250.0,
        "currency": "EUR",
        "hint": "Dépenses culturelles et sportives : cinéma, spectacle, musée, livre "
        "culturel, club/salle de sport, abonnement sportif, licence. Marchands type : "
        "UGC, FNAC (culturel), Basic-Fit, Decathlon, clubs sportifs.",
    },
    "APPRENTISSAGE": {
        "label": "Remboursement Apprentissage (Académie)",
        "reimbursement_rate": 1.0,
        "cap_reimbursed": 250.0,
        "currency": "EUR",
        "hint": "Dépenses de montée en compétences : formation, cours, conférence, "
        "certification, livre technique, matériel pédagogique, abonnement à un service "
        "d'IA (ChatGPT, Claude, Gemini…). Marchands type : OpenAI, Anthropic, Google, "
        "Udemy, Coursera, éditeurs techniques.",
    },
}
