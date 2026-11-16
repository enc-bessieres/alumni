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
