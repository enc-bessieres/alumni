"""
Les référentiels de l'école (issue #10, docs/01-audit-existant.md « Structure de l'école »).

Ce ne sont pas des données personnelles : ils ont leur place dans le dépôt.
Ce fichier ne dépend pas de Django : il sert au générateur de fausses données.
La migration 0002 en garde une copie figée : si tu modifies une liste ici, écris aussi
une nouvelle migration, sinon le test des données initiales échouera.
"""

SITES = ["ENC Bessières", "ENC Bessières Apprentissage"]

NIVEAUX = ["BTS", "Prépa"]

DIPLOMES = {
    "BTS": [
        "BTS ASSURANCE",
        "BTS CG",
        "BTS CI",
        "BTS COMMUNICATION",
        "BTS GPME",
        "BTS MCO",
        "BTS NDRC",
        "BTS PIM",
        "BTS SAM",
        "BTS SIO",
        "BTS TOURISME",
    ],
    # ATS (adaptation technicien supérieur) est une classe préparatoire : à confirmer.
    "Prépa": ["ATS", "D1", "D2", "DCG", "DCG2", "DCG3", "DSCG", "ECG", "ECT"],
}

# Référentiels d'administration (#39). Listes de départ, modifiables ensuite dans le back-office.
# Types de contrat : à valider avec Vera (offres). Secteurs : à valider avec Alex (profils).
TYPES_DE_CONTRAT = [
    "Alternance",
    "CDD",
    "CDI",
    "Indépendant",
    "Intérim",
    "Stage",
    "Volontariat (VIE, service civique)",
]

SECTEURS = [
    "Assurance",
    "Banque",
    "Commerce",
    "Communication et marketing",
    "Comptabilité et audit",
    "Conseil",
    "Enseignement et formation",
    "Fonction publique",
    "Immobilier",
    "Industrie",
    "Informatique et numérique",
    "Santé et social",
    "Tourisme et hôtellerie",
    "Transport et logistique",
    "Autre",
]
