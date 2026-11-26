"""
Export factice de l'annuaire Datalumni, au format du vrai `directory.csv` (issue #84).

Le format et les volumes sont ceux des exports réels, décrits dans docs/migration/export-reel.md.
Les personnes sont inventées (règle 1 d'AGENTS.md) : les tests, l'intégration continue et les
mesures de durée de l'import s'appuient sur ce fichier, jamais sur les fichiers réels.

Même graine = même fichier, au caractère près : deux imports à blanc sont comparables.
"""

import csv
import random
import unicodedata
import uuid
from collections import Counter
from datetime import UTC, datetime

from referentiels.donnees import DIPLOMES, SITES

# Les 28 colonnes de directory.csv, dans l'ordre du vrai fichier (vérifié par Alex sur #91) :
# notifications_registration est la dernière, contrairement au tableau de export-reel.md.
COLONNES = [
    "user_id", "external_ref", "first_name", "last_name", "birth_name", "email", "civility",
    "location", "phone", "account_status", "current_position", "current_company",
    "business_sector", "last_login", "last_profile_update", "account_activation_date",
    "category", "campus", "degree", "promotion_year", "import_date",
    "notifications_newsletter", "notifications_event", "visibility_recruiters",
    "visibility_directory", "job_search", "mentoring_role", "notifications_registration",
]  # fmt: skip

TOTAL = 6138
ACTIVES = 1233
# Catégorie : (comptes, dont activés). « / » sépare deux catégories, comme chez Datalumni.
CATEGORIES = {
    "Alumni": (5677, 1143),
    "Recruteur": (336, 17),
    "Enseignant": (79, 43),
    "Candidat": (16, 8),
    "Étudiant": (9, 9),
    "Équipe administrative": (4, 4),
    "Enseignant / Équipe administrative": (4, 4),
    "Alumni / Recruteur": (6, 4),
    "Alumni / Candidat": (2, 1),
    "": (5, 0),
}
# Les catégories sans diplôme : 428 comptes, plus 9 alumni tirés au sort = les 437 sans diplôme.
SANS_DIPLOME = {
    "Recruteur",
    "Enseignant",
    "Équipe administrative",
    "Enseignant / Équipe administrative",
    "",
}
# Les valeurs de business_sector (docs/migration/export-reel.md). La PR #76 les reprend dans le
# référentiel des secteurs : l'import les reliera par leur nom exact.
SECTEURS = [
    "Agences de communication, marketing, événementiel", "Agro-alimentaire",
    "Association non lucrative", "Automobile", "Autres", "Banque / Assurance / Finance",
    "Cabinet d'expertise comptable / Comptabilité", "Conseil / Audit",
    "Culture / Media / Divertissement", "Digital / Technologie",
    "Droit / Eco-gestion / Science Politique", "Enseignement / Formation / Recrutement",
    "Enseignement, Formation", "Entrepreneuriat / Start-up", "Environnement / Santé / Social",
    "Esthétique", "Grande distribution / Ventes", "Hôtellerie", "Industrie",
    "Mode / Luxe / Beauté", "Organisation internationale",
    "Publicité / Marketing / Communication", "Sciences / Recherche",
    "Secteur public et administration", "Tourisme / Hôtellerie / Restauration", "Travaux Publics",
]  # fmt: skip
CIVILITES = {"Mme.": 420, "M.": 390, "Madame": 190, "Monsieur": 160, "Non renseigné": 82}

PRENOMS = [
    "Inès", "Hugo", "Yasmine", "Théo", "Chloé", "Mamadou", "Lina", "Nathan", "Sarah", "Kevin",
    "Emma", "Lucas", "Aïcha", "Louis", "Camille", "Karim", "Jade", "Maxime", "Fatou", "Antoine",
    "Léa", "Rayan", "Manon", "Thomas", "Nour", "Julien", "Zoé", "Bilal", "Clara", "Adrien",
    "Mei", "Romain", "Sofia", "Enzo", "Amina", "Victor", "Élise", "Samir", "Anaïs", "Paul",
    "Lucie", "Mehdi", "Océane", "Quentin", "Salomé", "Yanis", "Marine", "Alexis", "Inaya", "Hamza",
    "Justine", "Florian", "Kenza", "Bastien", "Laura", "Ibrahima", "Pauline", "Damien", "Sana",
    "Arthur", "Margaux", "Moussa", "Elsa", "Benjamin", "Yuna", "Sacha", "Myriam", "Gabriel",
    "Noémie", "Ali", "Charlotte", "Dylan", "Linh", "Valentin", "Maëlle", "Ousmane", "Agathe",
    "Nicolas", "Rania", "Tom",
]  # fmt: skip
NOMS = [
    "Martin", "Benali", "Nguyen", "Diallo", "Lefèvre", "Moreau", "Haddad", "Petit", "Rousseau",
    "Chen", "Bernard", "Traoré", "Dubois", "Mansouri", "Laurent", "Pham", "Girard", "Kone",
    "Bonnet", "Wang", "Fontaine", "Cissé", "Mercier", "Bouaziz", "Faure", "Tran", "André",
    "Camara", "Garnier", "Li", "Chevalier", "Sow", "Lambert", "Amrani", "Roux", "Le Gall",
    "Morel", "Ndiaye", "Blanc", "Zhou", "Durand", "Belkacem", "Vo", "Keita", "Leroy", "Simon",
    "Hamidi", "Michel", "Liu", "Diop", "Lefebvre", "Gauthier", "Saïdi", "Perrin", "Huang",
    "Barry", "Robin", "Clément", "Meziane", "Masson", "Do", "Fofana", "Henry", "Nicolas",
    "Brahimi", "Mathieu", "Yang", "Coulibaly", "Lemoine", "Renard", "Ait Ali", "Gaillard",
    "Hoang", "Touré", "Picard", "Rey", "Bouchard", "Kaba", "De La Roche", "Marchand",
]  # fmt: skip
VILLES = [
    "Paris", "Montreuil", "Saint-Denis", "Boulogne-Billancourt", "Lyon", "Lille", "Nantes",
    "Vincennes", "Créteil", "Bordeaux",
]  # fmt: skip
POSTES = [
    "Comptable", "Assistant de gestion", "Chargée de communication", "Développeur",
    "Conseiller clientèle", "Gestionnaire de paie", "Commercial", "Auditrice junior",
]  # fmt: skip
ENTREPRISES = [
    "Cabinet Exemple Audit", "Exemple Assurances", "Banque Exemple", "Exemple Conseil",
    "Agence Exemple", "Exemple Numérique",
]  # fmt: skip

IMPORT_AVRIL = (datetime(2025, 4, 1, tzinfo=UTC), datetime(2025, 4, 30, tzinfo=UTC))  # 4601
IMPORT_OCTOBRE = (datetime(2025, 10, 1, tzinfo=UTC), datetime(2025, 10, 31, tzinfo=UTC))  # 715
OUVERTURE = datetime(2025, 3, 26, tzinfo=UTC)  # lancement de la plateforme Datalumni
RELEVE = datetime(2026, 11, 25, tzinfo=UTC)  # date des exports réels


def pour_adresse(texte):
    """« Le Gall » → « legall », « Inès » → « ines » : pour fabriquer les adresses."""
    sans_accents = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode()
    return "".join(c for c in sans_accents.lower() if c.isalnum())


def iso(moment):
    return moment.isoformat(timespec="seconds")  # « 2025-04-14T09:12:47+00:00 »


def booleen(valeur):
    return "True" if valeur else "False"


def generer_export_factice(graine=2026):
    """Renvoie les 6138 lignes de l'annuaire factice : une liste de dictionnaires (COLONNES)."""
    h = random.Random(graine)  # hasard reproductible : même graine, mêmes tirages

    def moment_entre(debut, fin):
        return debut + (fin - debut) * h.random()

    def parmi(indices, nombre):
        """`nombre` indices tirés au sort, sans remise."""
        return h.sample(sorted(indices), nombre)

    # 1. Les catégories, et le nombre de comptes activés dans chacune.
    lignes = [
        dict.fromkeys(COLONNES, "") | {"category": categorie}
        for categorie, (comptes, _) in CATEGORIES.items()
        for _ in range(comptes)
    ]
    h.shuffle(lignes)  # les catégories ne se suivent pas dans le fichier
    actives = set()
    for categorie, (_, dont_actives) in CATEGORIES.items():
        de_la_categorie = [i for i, ligne in enumerate(lignes) if ligne["category"] == categorie]
        actives.update(parmi(de_la_categorie, dont_actives))

    # 2. Les identités : chaque couple prénom + nom ne sert qu'une fois, sauf les 128 groupes
    # d'homonymes de l'export réel (125 paires et 3 trios = 259 comptes).
    identites = [(p, n) for p in PRENOMS for n in NOMS]
    h.shuffle(identites)
    groupes = [2] * 125 + [3] * 3
    noms, suivant = [], 0
    for taille in groupes:
        noms += [identites[suivant]] * taille
        suivant += 1
    noms += identites[suivant : suivant + TOTAL - len(noms)]
    h.shuffle(noms)
    porte = Counter(noms)
    uniques = [i for i in range(TOTAL) if porte[noms[i]] == 1]
    sans_nom = set(parmi(uniques, 4))  # pris hors des homonymes, pour garder les 128 groupes
    nom_normal = set(parmi(set(range(TOTAL)) - sans_nom, 98))  # 6036 en majuscules
    enc = set(parmi(range(TOTAL), 2048))  # adresses d'étudiant, imitées sur un faux domaine
    for i, ligne in enumerate(lignes):
        prenom, nom = noms[i]
        domaine = "enc-bessieres.exemple.test" if i in enc else "exemple.test"
        ligne["user_id"] = str(uuid.UUID(int=h.getrandbits(128), version=4))
        ligne["email"] = f"{pour_adresse(prenom)}.{pour_adresse(nom)}.{i + 1}@{domaine}"
        if i not in sans_nom:
            ligne["first_name"] = prenom
            ligne["last_name"] = nom if i in nom_normal else nom.upper()
        ligne["account_status"] = booleen(i in actives)
    for i in parmi(set(range(TOTAL)) - sans_nom, 55):
        lignes[i]["birth_name"] = h.choice(NOMS).upper()

    # 3. Origine et dates. Vide = inscrit seul (455 comptes, tous activés).
    # import_date est une date seule (AAAA-MM-JJ), comme account_activation_date ; le moment
    # exact est gardé à part pour tirer une activation qui vient après l'import.
    inscrits_seuls = set(parmi(actives, 455))
    importe_le = {}
    importes = [i for i in range(TOTAL) if i not in inscrits_seuls]
    h.shuffle(importes)
    for rang, i in enumerate(importes):
        if rang < 4601:
            moment = moment_entre(*IMPORT_AVRIL)
        elif rang < 4601 + 715:
            moment = moment_entre(*IMPORT_OCTOBRE)
        else:
            moment = moment_entre(OUVERTURE, RELEVE)
        importe_le[i] = moment
        lignes[i]["import_date"] = moment.date().isoformat()
    for i in actives:
        activation = moment_entre(importe_le.get(i, OUVERTURE), RELEVE)
        lignes[i]["account_activation_date"] = activation.date().isoformat()
        lignes[i]["last_login"] = iso(moment_entre(activation, RELEVE))
    for i in parmi(set(range(TOTAL)) - actives, 1252 - ACTIVES):
        lignes[i]["last_login"] = iso(moment_entre(OUVERTURE, RELEVE))
    for i in parmi(range(TOTAL), 5744):
        lignes[i]["last_profile_update"] = iso(moment_entre(OUVERTURE, RELEVE))

    # 4. Sites, diplômes et promos.
    tous_les_diplomes = [d for noms_ in DIPLOMES.values() for d in noms_]
    bts = DIPLOMES["BTS"]
    sans_site = set(parmi(range(TOTAL), 1160))
    deux_sites = set(parmi(set(range(TOTAL)) - sans_site, 52))
    for i, ligne in enumerate(lignes):
        if i in deux_sites:
            ligne["campus"] = " / ".join(SITES)
        elif i not in sans_site:
            ligne["campus"] = SITES[1] if h.random() < 0.15 else SITES[0]
    avec_diplome = [i for i in range(TOTAL) if lignes[i]["category"] not in SANS_DIPLOME]
    avec_diplome = sorted(set(avec_diplome) - set(parmi(avec_diplome, 9)))  # 5701 comptes
    plusieurs = set(parmi(avec_diplome, 121))  # un BTS puis une prépa, une seule année
    trois = set(parmi(plusieurs, 6))
    sans_annee = set(parmi(set(avec_diplome) - plusieurs, 10))
    for i in avec_diplome:
        ligne = lignes[i]
        if i in plusieurs:
            suite = ["DCG", "DSCG"] if i in trois else [h.choice(["DCG", "ECT", "D1"])]
            ligne["degree"] = " / ".join([h.choice(bts), *suite])
        else:
            ligne["degree"] = h.choice(tous_les_diplomes)
        if i not in sans_annee:
            etudiant = "Étudiant" in ligne["category"]
            annee = h.randint(2027, 2029) if etudiant else h.randint(1963, 2026)
            ligne["promotion_year"] = str(annee)
    # Les bornes de export-reel.md : la plus ancienne promo, et des étudiants jusqu'en 2029.
    avec_annee = [i for i in avec_diplome if lignes[i]["promotion_year"]]
    alumni = [i for i in avec_annee if "Étudiant" not in lignes[i]["category"]]
    etudiants = [i for i in avec_annee if "Étudiant" in lignes[i]["category"]]
    lignes[alumni[0]]["promotion_year"] = "1963"
    lignes[etudiants[0]]["promotion_year"] = "2029"

    # 5. Le profil, peu rempli comme chez Datalumni.
    civilites = parmi(range(TOTAL), sum(CIVILITES.values()))
    valeurs = [c for c, n in CIVILITES.items() for _ in range(n)]
    for i, civilite in zip(civilites, valeurs, strict=True):
        lignes[i]["civility"] = civilite
    for i in parmi(range(TOTAL), 663):
        lignes[i]["location"] = h.choice(VILLES)
    for i in parmi(range(TOTAL), 996):
        # Plage réservée à la fiction par l'ARCEP : 06 39 98 00 00 à 06 39 98 99 99.
        lignes[i]["phone"] = f"+3363998{h.randint(0, 9999):04d}"
    avec_poste = parmi(range(TOTAL), 357)
    for rang, i in enumerate(avec_poste):
        lignes[i]["current_position"] = h.choice(POSTES)
        lignes[i]["current_company"] = h.choice(ENTREPRISES)
        if rang < 340:
            lignes[i]["business_sector"] = h.choice(SECTEURS)

    # 6. Les préférences : (colonne, remplies, dont True).
    for colonne, remplies, vrais in [
        ("notifications_newsletter", 6128, 300),
        ("notifications_event", 6118, 5788),
        ("notifications_registration", 6118, 5779),
        ("visibility_recruiters", 6129, 642),
        ("visibility_directory", 6129, 6129),
        ("job_search", 289, 283),
    ]:
        remplis = parmi(range(TOTAL), remplies)
        for rang, i in enumerate(remplis):
            lignes[i][colonne] = booleen(rang < vrais)
    roles = ["mentor"] * 166 + ["mentee"] * 103 + ["mentor / mentee"] * 13
    for i, role in zip(parmi(range(TOTAL), len(roles)), roles, strict=True):
        lignes[i]["mentoring_role"] = role

    return lignes


def ecrire_export_factice(lignes, chemin):
    """Écrit les lignes comme le vrai export : UTF-8 avec BOM, virgules, une ligne d'en-tête."""
    with open(chemin, "w", encoding="utf-8-sig", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=COLONNES)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
