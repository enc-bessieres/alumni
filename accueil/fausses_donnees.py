"""
Fabrique de FAUX membres pour le développement et les démos (issue #10).

Aucune donnée réelle : les prénoms et les noms viennent des listes ci-dessous, et les adresses
sont en @exemple.test, un domaine réservé aux tests où aucune boîte n'existe.
Pas de bibliothèque comme Faker (règle du projet) : le module `random` de Python suffit.

Ce fichier ne touche pas à la base : il produit des dictionnaires, que la commande
`charger_donnees_dev` transforme en membres. On peut donc le tester sans base de données.

Il est déterministe : la même graine donne toujours les mêmes membres, ce qui rend les tests
et les démos reproductibles.
"""

import random
import unicodedata

from referentiels.donnees import DIPLOMES, SITES

PRENOMS = [
    "Adam", "Alice", "Amine", "Anaïs", "Arthur", "Camille", "Chloé", "Clément", "Emma", "Enzo",
    "Fatou", "Gabriel", "Hugo", "Inès", "Jade", "Jules", "Kenza", "Léa", "Lina", "Louis",
    "Lucas", "Manon", "Mathis", "Maëlle", "Nathan", "Noah", "Océane", "Rayan", "Sarah", "Théo",
    "Yanis", "Zoé",
]  # fmt: skip

NOMS = [
    "Bernard", "Bonnet", "Chevalier", "Da Silva", "Diallo", "Dubois", "Dupont", "Fournier",
    "Garcia", "Girard", "Haddad", "Lambert", "Laurent", "Lefèvre", "Martin", "Mercier",
    "Moreau", "N'Diaye", "Nguyen", "Petit", "Robin", "Roux", "Simon", "Traoré", "Vincent",
]  # fmt: skip

# Valeur du champ Membre.categorie -> nombre de membres, d'après l'annuaire actuel (issue #10).
REPARTITION = {
    "alumni": 1143,
    "enseignant": 50,
    "administratif": 10,
    "etudiant": 9,
    "candidat": 9,
    "recruteur": 1,
}
NOMBRE_PAR_DEFAUT = sum(REPARTITION.values())  # 1222, « environ 1300 » comme demandé

TOUS_LES_DIPLOMES = [nom for noms in DIPLOMES.values() for nom in noms]

# La promo est l'année de SORTIE : un alumni est sorti entre 1990 et 2026, un étudiant
# sortira en 2027 ou 2028.
PREMIERE_PROMO, DERNIERE_PROMO = 1990, 2026
PROMOS_ETUDIANT = (2027, 2028)


def en_ascii(texte):
    """« N'Diaye » -> « ndiaye », « Lefèvre » -> « lefevre » : de quoi écrire une adresse."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return "".join(c for c in sans_accents.lower() if c.isalnum())


def repartir(nombre):
    """
    Les catégories de `nombre` membres, dans les proportions de REPARTITION : exactement
    REPARTITION pour 1222 membres, et au plus près sinon (méthode du plus fort reste).
    """
    total = sum(REPARTITION.values())
    parts = {categorie: nombre * n / total for categorie, n in REPARTITION.items()}
    entiers = {categorie: int(part) for categorie, part in parts.items()}
    # Les places qui restent vont aux catégories qui ont perdu le plus en arrondissant.
    restes = sorted(parts, key=lambda c: parts[c] - entiers[c], reverse=True)
    for categorie in restes[: nombre - sum(entiers.values())]:
        entiers[categorie] += 1
    return [categorie for categorie, n in entiers.items() for _ in range(n)]


def generer_parcours(categorie, tirage):
    """Les diplômes d'un membre. Seuls les alumni et les étudiants en ont un."""
    if categorie == "etudiant":
        diplome = tirage.choice(TOUS_LES_DIPLOMES)
        return [
            {
                "diplome": diplome,
                "site": tirage.choice(SITES),
                "promo": tirage.choice(PROMOS_ETUDIANT),
            }
        ]
    if categorie != "alumni":
        return []  # enseignant, équipe administrative, candidat, recruteur : pas de promo
    # Environ 1 alumni sur 5 a deux diplômes (par exemple un BTS puis un DCG) :
    # le second est obtenu 1 à 3 ans après le premier, jamais avant.
    deux = tirage.random() < 0.2
    premiere = tirage.randint(PREMIERE_PROMO, DERNIERE_PROMO - (3 if deux else 0))
    promos = [premiere, premiere + tirage.randint(1, 3)] if deux else [premiere]
    diplomes = tirage.sample(TOUS_LES_DIPLOMES, len(promos))
    return [
        {"diplome": diplome, "site": tirage.choice(SITES), "promo": promo}
        for diplome, promo in zip(diplomes, promos, strict=True)
    ]


def generer_membres(nombre=NOMBRE_PAR_DEFAUT, graine=2026):
    """Renvoie `nombre` faux membres, sous forme de dictionnaires."""
    tirage = random.Random(graine)  # un générateur à nous : ne dépend pas du reste du programme
    categories = repartir(nombre)
    tirage.shuffle(categories)  # sinon les 1143 alumni viendraient tous en premier

    membres = []
    for numero, categorie in enumerate(categories, start=1):
        prenom = tirage.choice(PRENOMS)
        nom = tirage.choice(NOMS)
        parcours = generer_parcours(categorie, tirage)
        membres.append(
            {
                "prenom": prenom,
                "nom": nom,
                # Le numéro rend chaque adresse unique, même si deux membres ont le même nom.
                "email": f"{en_ascii(prenom)}.{en_ascii(nom)}.{numero}@exemple.test",
                "categorie": categorie,
                "parcours": parcours,  # devient des Formation dans charger_donnees_dev
            }
        )
    return membres
