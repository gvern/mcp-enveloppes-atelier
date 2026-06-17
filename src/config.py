"""Règles des deux enveloppes AVISIA + disposition du formulaire.

Basé sur les vrais templates :
- "AVISIA modèle-subvention 2025.xlsx"        → enveloppe CE
- "TEMPLATE PARIS NDF Remboursement apprentissage.xlsx" → enveloppe APPRENTISSAGE

Plafond = 250 € sur le montant REMBOURSÉ (pris en charge).
  CE            : remboursé à 50 %  → engageable ≈ 500 €
  APPRENTISSAGE : remboursé à 100 % → engageable = 250 €
"""

# Disposition commune des deux formulaires (onglet "Feuil1")
FORM = {
    "tab": "Feuil1",
    "nom_cell": "B10",
    "prenom_cell": "B11",
    "desc_col": "A",       # DESCRIPTIF DES FACTURES
    "amount_col": "B",     # MONTANT ENGAGE
    "first_line_row": 15,  # première ligne de facture
    "last_line_row": 28,   # dernière ligne (14 lignes max)
    "total_cell": "B29",   # = SUBTOTAL(109, B15:B28), auto-calculé
}

ENVELOPES = {
    "CE": {
        "label": "Subvention CE",
        "reimbursement_rate": 0.5,
        "cap_reimbursed": 250.0,
        "currency": "EUR",
        # Confirmé par le template : "dépenses culturelles et sportives"
        "eligible": [
            "culture",
            "sport",
            "abonnement-sport",  # salle de sport, club, licence sportive
            "loisirs",
            "spectacle",
            "cinema",
            "musee",
            "sport-licence",
        ],
        "excludes": [],
        "hint": "Dépenses culturelles et sportives : cinéma, spectacle, musée, livre culturel, "
        "club/salle de sport, abonnement sportif, licence. Marchands type : UGC, FNAC (culturel), "
        "Basic-Fit, Decathlon, clubs sportifs.",
    },
    "APPRENTISSAGE": {
        "label": "Remboursement Apprentissage (Académie)",
        "reimbursement_rate": 1.0,
        "cap_reimbursed": 250.0,
        "currency": "EUR",
        # TODO Nathan : confirmer les catégories éligibles de l'apprentissage
        # "abonnement-ia" = abonnements aux IA (ChatGPT, Claude, Gemini, etc.)
        "eligible": [
            "formation",
            "livre",
            "conference",
            "certification",
            "cours",
            "materiel-pedagogique",
            "abonnement-ia",
        ],
        "excludes": [],
        "hint": "Dépenses de montée en compétences : formation, cours, conférence, "
        "certification, livre technique, matériel pédagogique, abonnement à un service d'IA. "
        "Marchands type : OpenAI/ChatGPT, Anthropic/Claude, Google Gemini, Udemy, Coursera, éditeurs techniques.",
    },
}

# Noms de marchands / mots-clés mappés directement vers une enveloppe (sans passer par
# le LLM). Matché par sous-ensemble de tokens, comme les catégories éligibles.
ALIASES = {
    # IA → APPRENTISSAGE
    "chatgpt": "APPRENTISSAGE",
    "openai": "APPRENTISSAGE",
    "claude": "APPRENTISSAGE",
    "anthropic": "APPRENTISSAGE",
    "gemini": "APPRENTISSAGE",
    "mistral": "APPRENTISSAGE",
    "copilot": "APPRENTISSAGE",
    "perplexity": "APPRENTISSAGE",
    "cursor": "APPRENTISSAGE",
    # Sport → CE
    "basic-fit": "CE",
    "fitness park": "CE",
    "decathlon": "CE",
}
