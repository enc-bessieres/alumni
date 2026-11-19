"""
Export factice au format Datalumni (règle 1 d'AGENTS.md : aucune donnée réelle).

Tant que l'échantillon de Datalumni n'est pas arrivé, l'import se construit sur ce fichier.
Le format est une HYPOTHÈSE, décrite dans docs/migration/export-factice.md. Quand le vrai
format arrive, on adapte ce fichier et la lecture de l'import, pas le reste.

Même graine = même export, au caractère près : deux migrations à blanc sont comparables.
"""

import copy
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
    # Les défauts de la plateforme actuelle (issue #10, docs/01 § 2) : peu de profils remplis.
    part_photo: float = 0.24
    part_experience: float = 0.28
    part_localisation: float = 0.53
    # Les cas difficiles (docs/06-points-durs.md, § 1). Un membre n'a qu'un seul cas.
    jamais_actives: int = 450
    emails_morts: int = 40  # parmi les jamais activés
    sans_email: int = 5  # parmi les jamais activés
    google_seulement: int = 30
    linkedin_seulement: int = 10
    google_en_plus: int = 60
    doublons: int = 25
    homonymes: int = 5
    en_attente: int = 10
    refuses: int = 5
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


def commune(nom, departement, region, pays, lat, lng):
    return {
        "commune": nom,
        "departement": departement,
        "region": region,
        "pays": pays,
        "lat": lat,
        "lng": lng,
    }


COMMUNES = [
    commune("Paris", "75", "Île-de-France", "France", 48.8835, 2.3219),
    commune("Clichy", "92", "Île-de-France", "France", 48.9045, 2.306),
    commune("Saint-Denis", "93", "Île-de-France", "France", 48.9362, 2.3574),
    commune("Versailles", "78", "Île-de-France", "France", 48.8049, 2.1204),
    commune("Lyon", "69", "Auvergne-Rhône-Alpes", "France", 45.764, 4.8357),
    commune("Lille", "59", "Hauts-de-France", "France", 50.6292, 3.0573),
    commune("Bordeaux", "33", "Nouvelle-Aquitaine", "France", 44.8378, -0.5792),
    commune("Montréal", None, None, "Canada", 45.5019, -73.5674),
    commune("Casablanca", None, None, "Maroc", 33.5731, -7.5898),
]
# Des employeurs visiblement inventés, pour qu'aucun ne soit pris pour une vraie entreprise.
ORGANISATIONS = [
    "Cabinet Exemple Audit", "Banque Fictive du Nord", "Exemple Assurances", "Studio Factice",
    "Logistique Exemple", "Agence Imaginaire", "Mairie d'Exempleville", "Hôtel Fictif",
]  # fmt: skip
POSTES = [
    "Comptable", "Assistant de gestion", "Chargé de clientèle", "Développeur", "Commercial",
    "Contrôleur de gestion", "Auditeur", "Chargé de communication", "Conseiller en assurance",
]  # fmt: skip
SECTEURS = [
    "Comptabilité", "Banque", "Assurance", "Informatique", "Commerce", "Communication",
    "Transport", "Tourisme", "Fonction publique",
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

    def experience():
        debut = h.randint(config.promo_min, config.promo_max - 1)
        en_cours = h.random() < 0.4
        return {
            "intitule": h.choice(POSTES),
            "organisation": h.choice(ORGANISATIONS),
            "debut": debut,
            "fin": None if en_cours else min(config.promo_max, debut + h.randint(1, 6)),
            "poste_actuel": en_cours,
            "secteur": h.choice(SECTEURS),
            "lieu": h.choice(COMMUNES)["commune"],
        }

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
    # Chaque couple prénom + nom ne sert qu'une fois : seuls les doublons et homonymes voulus
    # (étape 5) se ressemblent.
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

    # Peu de profils remplis, comme aujourd'hui : exactement 24 %, 28 % et 53 % des membres.
    def part(proportion):
        return h.sample(range(len(membres)), round(len(membres) * proportion))

    for i in part(config.part_photo):
        # Une adresse en .test : le site affichera les initiales, comme pour un membre sans photo.
        membres[i]["metadata"]["photo"] = (
            f"https://media.exemple.test/photos/{membres[i]['uuid']}.jpg"
        )
    for i in part(config.part_experience):
        membres[i]["experiences"] = [experience() for _ in range(h.randint(1, 3))]
    for i in part(config.part_localisation):
        membres[i]["metadata"]["localisation"] = dict(h.choice(COMMUNES))

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

    # 5. Les cas difficiles de docs/06-points-durs.md, § 1. Un membre n'a qu'un seul cas.
    pris = set()

    def tirer(condition, n):
        """Tire n membres (leurs numéros) qui vérifient la condition et n'ont pas encore de cas."""
        candidats = [i for i, m in enumerate(membres) if i not in pris and condition(m, i)]
        if len(candidats) < n:
            raise ValueError(f"Configuration impossible : il manque {n - len(candidats)} membres")
        choisis = h.sample(candidats, n)
        pris.update(choisis)
        return choisis

    def inutilisable():
        return "!" + texte(40)  # ce que Django écrit quand il n'y a pas de mot de passe

    def importe(m, i):
        return m["origine"] == "import"

    def inscrit(m, i):
        return m["origine"] == "inscription"

    def alumni(m, i):
        return m["categorie"] == "Alumni"

    def masque_inscrit(m, i):
        return i >= nb_visibles and inscrit(m, i)

    # Importés jamais activés : pas de mot de passe, jamais connectés. Certains ont une adresse
    # morte (convention du factice : le vrai export ne le dira pas) ou pas d'adresse du tout.
    for k, i in enumerate(tirer(importe, config.jamais_actives)):
        m = membres[i]
        m.update(password=inutilisable(), derniere_connexion=None, email_verifie=False)
        m["consentements"]["cgu_acceptees_le"] = None
        if k < config.emails_morts:
            m["email"] = m["email"].replace("@exemple.test", "@mort.exemple.test")
        elif k < config.emails_morts + config.sans_email:
            m["email"] = ""

    for i in tirer(masque_inscrit, config.en_attente):
        membres[i]["statut"] = "en_attente"
    for i in tirer(masque_inscrit, config.refuses):
        membres[i]["statut"] = "refuse"

    def google():
        return {"fournisseur": "google", "sub": texte(21, "0123456789")}

    def linkedin():
        return {"fournisseur": "linkedin", "sub": texte(10)}

    for i in tirer(inscrit, config.google_seulement):
        membres[i].update(password=inutilisable(), liaisons=[google()])
    for i in tirer(inscrit, config.linkedin_seulement):
        membres[i].update(password=inutilisable(), liaisons=[linkedin()])
    for i in tirer(inscrit, config.google_en_plus):
        membres[i]["liaisons"].append(google())

    # Doublon : une personne importée s'est réinscrite seule, avec une autre adresse.
    originaux = tirer(lambda m, i: importe(m, i) and alumni(m, i), config.doublons)
    copies = tirer(lambda m, i: inscrit(m, i) and alumni(m, i) and i < nb_visibles, config.doublons)
    for i_original, i_copie in zip(originaux, copies, strict=True):
        original, copie = membres[i_original], membres[i_copie]
        prenom, nom = original["metadata"]["prenom"], original["metadata"]["nom"]
        copie["metadata"].update(prenom=prenom, nom=nom)
        copie["email"] = adresse(prenom, nom, i_copie + 1)
        copie["groupes"] = copy.deepcopy(original["groupes"])

    # Homonyme : même nom, mais un autre diplôme. Ce n'est PAS un doublon.
    portent_le_nom = tirer(alumni, config.homonymes)
    homonymes = tirer(alumni, config.homonymes)
    for i_autre, i_homonyme in zip(portent_le_nom, homonymes, strict=True):
        autre, homonyme = membres[i_autre], membres[i_homonyme]
        prenom, nom = autre["metadata"]["prenom"], autre["metadata"]["nom"]
        homonyme["metadata"].update(prenom=prenom, nom=nom)
        homonyme["email"] = adresse(prenom, nom, i_homonyme + 1)
        ses_diplomes = {g["groupe_uuid"] for g in autre["groupes"]}
        autre_diplome = h.choice([d for d in diplomes if d["uuid"] not in ses_diplomes])
        homonyme["groupes"] = [
            homonyme["groupes"][0],  # son site
            {
                "groupe_uuid": autre_diplome["uuid"],
                "timeline": {"annee": h.randint(config.promo_min, config.promo_max)},
            },
        ]

    return {"format": FORMAT, "groupes": groupes, "membres": membres}
