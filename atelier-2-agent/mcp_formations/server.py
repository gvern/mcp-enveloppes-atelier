"""Mini MCP fictif — catalogue formations/certifications AVISIA MOCKÉ (aucune donnée réelle).

⚙️ PLOMBERIE fournie pour l'atelier 2 — sert de DEUXIÈME MCP pour l'exercice 4 (gestion de
plusieurs outils côté agent). Ne pas modifier pendant l'atelier : ce n'est pas l'objet de
l'exercice (le protocole MCP a déjà été vu en atelier 1). Ce MCP est fourni "tel quel",
complet, pas un squelette à trous.

Toutes les données ci-dessous sont INVENTÉES à but pédagogique — pas d'appel externe, pas
de donnée réelle AVISIA (ni catalogue RH réel, ni prix réels, ni organismes partenaires
réels).

Lancer seul (debug) :  uv run mcp dev mcp_formations/server.py
"""

from mcp.server.fastmcp import FastMCP

INSTRUCTIONS = """\
Catalogue FICTIF de formations/certifications internes AVISIA — données mockées, aucun
appel réseau réel. Sert à répondre aux questions du type « quelle formation sur X ? » ou
« combien coûte telle certification ? ».

Le prix TTC renvoyé par ce MCP est à comparer au budget restant de l'enveloppe
APPRENTISSAGE (autre MCP, atelier 1 — outil get_balance) AVANT de recommander une
inscription : une formation peut dépasser le reste remboursable même si elle a l'air
raisonnable.
"""

mcp = FastMCP("formations-avisia", instructions=INSTRUCTIONS)

# Jeu de données 100 % inventé — à but pédagogique uniquement.
_MOCK_FORMATIONS = [
    {
        "id": "genai-prompt-101",
        "titre": "Prompt Engineering & Agents — les fondamentaux",
        "categorie": "GenAI/LLM",
        "format": "e-learning",
        "duree_heures": 8,
        "prix_ttc": 190.0,
        "organisme": "DataCamp Academy",
        "descriptif": (
            "Écrire des prompts efficaces, structurer un system prompt, et concevoir un "
            "premier agent avec tool-calling. Cas pratiques sur des cas d'usage type "
            "assistant métier."
        ),
    },
    {
        "id": "genai-mcp-201",
        "titre": "Protocoles agentiques : Model Context Protocol (MCP) en pratique",
        "categorie": "GenAI/LLM",
        "format": "e-learning",
        "duree_heures": 12,
        "prix_ttc": 340.0,
        "organisme": "OpenClass Pro",
        "descriptif": (
            "Concevoir et exposer des outils via MCP, brancher un client agentique "
            "multi-serveurs, bonnes pratiques de sécurité et de conception de tools."
        ),
    },
    {
        "id": "cloud-gcp-ace",
        "titre": "Certification Google Cloud — Associate Cloud Engineer",
        "categorie": "Cloud",
        "format": "certification",
        "duree_heures": 24,
        "prix_ttc": 165.0,
        "organisme": "Google Cloud",
        "descriptif": (
            "Préparation + passage de la certification ACE : déploiement, gestion et "
            "supervision d'applications sur Google Cloud Platform."
        ),
    },
    {
        "id": "cloud-aws-saa",
        "titre": "Certification AWS — Solutions Architect Associate",
        "categorie": "Cloud",
        "format": "certification",
        "duree_heures": 30,
        "prix_ttc": 195.0,
        "organisme": "AWS Training",
        "descriptif": (
            "Concevoir des architectures distribuées résilientes et économiques sur AWS. "
            "Prépare au passage de l'examen officiel SAA-C03."
        ),
    },
    {
        "id": "data-eng-spark",
        "titre": "Data Engineering avec Apache Spark & Airflow",
        "categorie": "Data Engineering",
        "format": "présentiel",
        "duree_heures": 21,
        "prix_ttc": 890.0,
        "organisme": "DataCraft Institute",
        "descriptif": (
            "Concevoir des pipelines de traitement de données à grande échelle : "
            "ingestion, transformation distribuée (Spark), orchestration (Airflow)."
        ),
    },
    {
        "id": "data-eng-dbt",
        "titre": "Modélisation analytique avec dbt",
        "categorie": "Data Engineering",
        "format": "e-learning",
        "duree_heures": 10,
        "prix_ttc": 220.0,
        "organisme": "OpenClass Pro",
        "descriptif": (
            "Construire des transformations SQL versionnées et testées avec dbt, "
            "intégration à un entrepôt de données cloud."
        ),
    },
    {
        "id": "cert-scrum-po",
        "titre": "Certification Product Owner (Scrum)",
        "categorie": "Certification",
        "format": "certification",
        "duree_heures": 16,
        "prix_ttc": 590.0,
        "organisme": "Scrum Alliance France",
        "descriptif": (
            "Rôle du Product Owner, gestion de backlog, priorisation, cérémonies Scrum. "
            "Certification reconnue à l'issue de la formation."
        ),
    },
    {
        "id": "lang-english-b2",
        "titre": "Anglais professionnel — préparation TOEIC (niveau B2)",
        "categorie": "Langues",
        "format": "e-learning",
        "duree_heures": 20,
        "prix_ttc": 240.0,
        "organisme": "LinguaSkills",
        "descriptif": (
            "Renforcement de l'anglais professionnel à l'écrit et à l'oral, préparation "
            "ciblée au format de l'examen TOEIC."
        ),
    },
    {
        "id": "softskills-public-speaking",
        "titre": "Prise de parole en public et présentation client",
        "categorie": "Soft skills",
        "format": "présentiel",
        "duree_heures": 7,
        "prix_ttc": 210.0,
        "organisme": "TalentUp Formation",
        "descriptif": (
            "Structurer un pitch, gérer le stress, capter l'attention d'un auditoire lors "
            "de soutenances ou de présentations client."
        ),
    },
    {
        "id": "genai-conf-2026",
        "titre": "Conférence tech — GenAI & agents en entreprise 2026",
        "categorie": "GenAI/LLM",
        "format": "présentiel",
        "duree_heures": 6,
        "prix_ttc": 95.0,
        "organisme": "DevFest Community",
        "descriptif": (
            "Journée de conférences et retours d'expérience sur le déploiement d'agents "
            "IA en production dans des SSII et grands groupes."
        ),
    },
]

_FORMATIONS_BY_ID = {f["id"]: f for f in _MOCK_FORMATIONS}


@mcp.tool()
def list_formations(categorie: str | None = None) -> dict:
    """Liste les formations du catalogue FICTIF, filtrable par catégorie.

    Catégories disponibles dans le mock : "GenAI/LLM", "Cloud", "Data Engineering",
    "Certification", "Langues", "Soft skills". Si `categorie` est omise, renvoie tout le
    catalogue. Renvoie {count, formations} — chaque formation avec tous ses champs.
    """
    if categorie:
        key = categorie.strip().lower()
        results = [f for f in _MOCK_FORMATIONS if f["categorie"].lower() == key]
    else:
        results = list(_MOCK_FORMATIONS)
    return {"count": len(results), "formations": results}


@mcp.tool()
def search_formations(query: str) -> dict:
    """Recherche texte libre dans le catalogue FICTIF (titre, descriptif, organisme).

    Recherche insensible à la casse, simple sous-chaîne (pas de fuzzy matching). Utile pour
    des questions type « une formation sur le prompt engineering » ou « certification
    cloud ». Renvoie {count, formations}.
    """
    needle = query.strip().lower()
    results = [
        f
        for f in _MOCK_FORMATIONS
        if needle in f["titre"].lower()
        or needle in f["descriptif"].lower()
        or needle in f["organisme"].lower()
        or needle in f["categorie"].lower()
    ]
    return {"count": len(results), "formations": results}


@mcp.tool()
def get_formation(id: str) -> dict:
    """Détail complet d'une formation FICTIVE à partir de son `id`.

    Renvoie tous les champs (titre, categorie, format, duree_heures, prix_ttc, organisme,
    descriptif), ou un message d'erreur si l'id ne fait pas partie du jeu de données mocké.
    """
    formation = _FORMATIONS_BY_ID.get(id.strip())
    if formation is None:
        return {
            "id": id,
            "erreur": "id hors du jeu de données mocké — utilise list_formations ou "
            "search_formations pour retrouver l'id exact",
        }
    return formation


if __name__ == "__main__":
    mcp.run()  # stdio uniquement — ce MCP est piloté par l'agent, pas par Claude Desktop
