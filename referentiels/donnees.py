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
# Ce sont celles de Datalumni (docs/migration/export-reel.md), écrites à l'identique : l'import
# relie le secteur d'un membre ou d'une offre, et le type d'une offre, par le nom exact.
# « / » fait partie de certains noms (« Conseil / Audit ») : ne jamais le découper.
TYPES_DE_CONTRAT = [
    "CDI",
    "Alternance",
    "Stage",
    "CDD",
    "Autre",
]

SECTEURS = [
    "Agences de communication, marketing, événementiel",
    "Agro-alimentaire",
    "Association non lucrative",
    "Automobile",
    "Autres",
    "Banque / Assurance / Finance",
    "Cabinet d'expertise comptable / Comptabilité",
    "Conseil / Audit",
    "Culture / Media / Divertissement",
    "Digital / Technologie",
    "Droit / Eco-gestion / Science Politique",
    "Enseignement / Formation / Recrutement",
    "Enseignement, Formation",
    "Entrepreneuriat / Start-up",
    "Environnement / Santé / Social",
    "Esthétique",
    "Grande distribution / Ventes",
    "Hôtellerie",
    "Industrie",
    "Mode / Luxe / Beauté",
    "Organisation internationale",
    "Publicité / Marketing / Communication",
    "Sciences / Recherche",
    "Secteur public et administration",
    "Tourisme / Hôtellerie / Restauration",
    "Travaux Publics",
]
