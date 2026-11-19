"""
Export factice au format Datalumni (règle 1 d'AGENTS.md : aucune donnée réelle).

Tant que l'échantillon de Datalumni n'est pas arrivé, l'import se construit sur ce fichier.
Le format est une HYPOTHÈSE, décrite dans docs/migration/export-factice.md. Quand le vrai
format arrive, on adapte ce fichier et la lecture de l'import, pas le reste.

Même graine = même export, au caractère près : deux migrations à blanc sont comparables.
"""

import random
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from django.contrib.auth.hashers import PBKDF2PasswordHasher

from referentiels.donnees import DIPLOMES, NIVEAUX, SITES

FORMAT = "datalumni-factice/1"

OUVERTURE = datetime(2025, 3, 26, tzinfo=UTC)  # lancement de la plateforme Datalumni
VAGUE_IMPORT = (datetime(2025, 4, 1, tzinfo=UTC), datetime(2025, 4, 30, tzinfo=UTC))
RELEVE = datetime(2026, 11, 8, tzinfo=UTC)  # date du relevé de l'annuaire

ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@dataclass(frozen=True)
class ConfigExport:
    """Les volumes de l'annuaire relevé le 8 novembre 2026 (docs/01-audit-existant.md, § 2)."""

    graine: int = 2026
    visibles: dict = field(
        default_factory=lambda: {
            "Alumni": 1143,
            "Enseignant": 50,
            "Équipe administrative": 10,
            "Étudiant": 9,
            "Candidat": 9,
            "Recruteur": 1,
        }
    )
    # Les catégories du relevé font 1222, alors que l'annuaire annonce 1214 membres : on garde
    # les catégories. Le total réel est inconnu (« environ 1300 ») : 78 masqués pour y arriver.
    masques: int = 78
    importes: int = 784
    plusieurs_diplomes: int = 120
    promo_min: int = 1990
    promo_max: int = 2026
    # 1 000 000 chez Django 5.2 : trop lent pour 1 300 comptes. Django lit ce nombre dans
    # l'empreinte, et la ré-enregistre au réglage actuel à la première connexion.
    iterations: int = 1000


CONFIG_PAR_DEFAUT = ConfigExport()

PRENOMS = [
    "Inès", "Hugo", "Yasmine", "Théo", "Chloé", "Mamadou", "Lina", "Nathan", "Sarah", "Kevin",
    "Emma", "Lucas", "Aïcha", "Louis", "Camille", "Karim", "Jade", "Maxime", "Fatou", "Antoine",
    "Léa", "Rayan", "Manon", "Thomas", "Nour", "Julien", "Zoé", "Bilal", "Clara", "Adrien",
    "Mei", "Romain", "Sofia", "Enzo", "Amina", "Victor", "Élise", "Samir", "Anaïs", "Paul",
]  # fmt: skip
NOMS = [
    "Martin", "Benali", "Nguyen", "Diallo", "Lefèvre", "Moreau", "Haddad", "Petit", "Rousseau",
    "Chen", "Bernard", "Traoré", "Dubois", "Mansouri", "Laurent", "Pham", "Girard", "Kone",
    "Bonnet", "Wang", "Fontaine", "Cissé", "Mercier", "Bouaziz", "Faure", "Tran", "André",
    "Camara", "Garnier", "Li", "Chevalier", "Sow", "Lambert", "Amrani", "Roux", "Le Gall",
    "Morel", "Ndiaye", "Blanc", "Zhou",
]  # fmt: skip


def pour_adresse(texte):
    """« Le Gall » → « legall », « Inès » → « ines » : pour fabriquer les adresses."""
    sans_accents = unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode()
    return "".join(c for c in sans_accents.lower() if c.isalnum())


def adresse(prenom, nom, numero, domaine="exemple.test"):
    return f"{pour_adresse(prenom)}.{pour_adresse(nom)}.{numero}@{domaine}"


def iso(moment):
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def generer_export_factice(config=CONFIG_PAR_DEFAUT, mot_de_passe="motdepasse-factice"):
    """Renvoie l'export factice sous forme de dictionnaire, prêt à écrire en JSON."""
    h = random.Random(config.graine)  # hasard reproductible : même graine, mêmes tirages
    hasher = PBKDF2PasswordHasher()  # celui de Django, donc le même format que chez Authentik

    def texte(longueur, alphabet=ALPHANUM):
        return "".join(h.choice(alphabet) for _ in range(longueur))

    def nouvel_uuid():
        return str(uuid.UUID(int=h.getrandbits(128), version=4))

    def moment_entre(debut, fin):
        return debut + (fin - debut) * h.random()

    # 1. Les groupes, avec les mêmes noms que referentiels/donnees.py.
    groupes = []

    def groupe(type_, nom, parent_uuid=None):
        g = {"uuid": nouvel_uuid(), "type": type_, "nom": nom, "parent_uuid": parent_uuid}
        groupes.append(g)
        return g

    site_bessieres, site_apprentissage = [groupe("site", nom) for nom in SITES]
    diplomes = []
    for niveau in NIVEAUX:
        n = groupe("niveau", niveau)
        diplomes += [groupe("diplome", nom, n["uuid"]) for nom in DIPLOMES[niveau]]
    dcg = next(d for d in diplomes if d["nom"] == "DCG")
    premiers_diplomes = [d for d in diplomes if d is not dcg]

    # 2. Les membres : d'abord les visibles de l'annuaire, puis les masqués.
    categories = [c for c, n in config.visibles.items() for _ in range(n)]
    nb_visibles = len(categories)
    categories += ["Alumni"] * config.masques
    # Chaque couple prénom + nom ne sert qu'une fois : deux membres ne se ressemblent pas par
    # hasard (les doublons et homonymes voulus arrivent avec les cas difficiles).
    identites = [(prenom, nom) for prenom in PRENOMS for nom in NOMS]
    h.shuffle(identites)
    if len(categories) > len(identites):
        raise ValueError("Pas assez de prénoms et de noms pour ce nombre de membres")

    membres = []
    for i, categorie in enumerate(categories):
        prenom, nom = identites[i]
        inscription = moment_entre(OUVERTURE, RELEVE)
        site = site_apprentissage if h.random() < 0.15 else site_bessieres
        appartenances = [{"groupe_uuid": site["uuid"], "timeline": None}]
        if categorie in ("Alumni", "Étudiant"):
            if categorie == "Alumni":
                annee = h.randint(config.promo_min, config.promo_max)
            else:
                annee = h.randint(config.promo_max + 1, config.promo_max + 2)  # encore en cours
            diplome = h.choice(premiers_diplomes)
            appartenances.append({"groupe_uuid": diplome["uuid"], "timeline": {"annee": annee}})
        membres.append(
            {
                "uuid": nouvel_uuid(),
                "email": adresse(prenom, nom, i + 1),
                "email_verifie": True,
                "password": hasher.encode(mot_de_passe, texte(22), config.iterations),
                "origine": "inscription",
                "date_inscription": iso(inscription),
                "derniere_connexion": iso(moment_entre(inscription, RELEVE)),
                "statut": "accepte",
                "visible_annuaire": i < nb_visibles,
                "categorie": categorie,
                "metadata": {
                    "civilite": h.choice(["M.", "Mme", None]),
                    "prenom": prenom,
                    "nom": nom,
                    "nom_naissance": None,
                    "photo": None,
                    "localisation": None,
                },
                "experiences": [],
                "groupes": appartenances,
                "liaisons": [],
                "consentements": {
                    "cgu_acceptees_le": iso(inscription),
                    "newsletter": h.random() < 0.24,
                },
            }
        )

    # 3. L'origine : la vague d'import d'avril 2025, le reste inscrit seul.
    for i in h.sample(range(len(membres)), config.importes):
        m = membres[i]
        import_ = moment_entre(*VAGUE_IMPORT)
        m["origine"] = "import"
        m["date_inscription"] = m["consentements"]["cgu_acceptees_le"] = iso(import_)
        m["derniere_connexion"] = iso(moment_entre(import_, RELEVE))

    # 4. Plusieurs diplômes : un premier diplôme suivi d'un DCG trois ans plus tard.
    def promo(m):
        return next(g["timeline"]["annee"] for g in m["groupes"] if g["timeline"])

    poursuivants = [m for m in membres if m["categorie"] == "Alumni" and promo(m) <= 2023]
    for m in h.sample(poursuivants, config.plusieurs_diplomes):
        m["groupes"].append({"groupe_uuid": dcg["uuid"], "timeline": {"annee": promo(m) + 3}})

    return {"format": FORMAT, "groupes": groupes, "membres": membres}
