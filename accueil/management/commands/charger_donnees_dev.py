"""
Charge les fausses données de développement (issue #10). Jamais de données réelles.

Les sites, niveaux et diplômes sont déjà dans la base : la migration 0002 de `referentiels`
les crée. Cette commande ajoute des faux membres et leur parcours (diplômes et promos).

Elle est rejouable : la relancer remet la base dans le même état. Elle efface d'abord les
faux membres (adresse de la forme prenom.nom.12@exemple.test), puis les recrée. Les comptes
créés à la main (createsuperuser, back-office) ne sont jamais touchés. Un faux membre passé
dans l'équipe est effacé comme les autres : les droits se donnent à un compte créé à la main.

Tous les faux membres ont le même mot de passe, connu de l'équipe : le réglage
MOT_DE_PASSE_DONNEES_DEV de config/settings.py, lu dans le fichier .env (voir .env.example).
Leur adresse est marquée vérifiée : ils se connectent directement par /compte/login/.

Sauf deux sur dix, pour essayer la première connexion après la bascule (#85) : ils sont
« importés de Datalumni », sans mot de passe et avec une adresse non vérifiée, comme le fera
l'import. Le 9ᵉ de chaque dizaine était inscrit chez Datalumni (compte activé), le 10ᵉ ne
l'était pas (compte non activé, absent de l'annuaire).
"""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accueil.fausses_donnees import NOMBRE_PAR_DEFAUT, generer_membres
from referentiels.models import Diplome, Formation, Site

# Première connexion (#85) : rang du faux membre dans sa dizaine -> compte activé chez Datalumni.
IMPORTES_SANS_MOT_DE_PASSE = {8: True, 9: False}

# Les adresses que fabrique fausses_donnees.py, et seulement elles : « admin@exemple.test »
# n'a pas de numéro, il n'est donc jamais effacé.
FAUSSES_ADRESSES = r"^[a-z0-9]+\.[a-z0-9]+\.[0-9]+@exemple\.test$"


class Command(BaseCommand):
    help = "Charge les fausses données de développement. Jamais de données réelles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--nombre",
            type=int,
            default=NOMBRE_PAR_DEFAUT,
            help=f"nombre de faux membres ({NOMBRE_PAR_DEFAUT} par défaut, comme l'annuaire)",
        )
        parser.add_argument(
            "--graine", type=int, default=2026, help="graine du tirage (2026 par défaut)"
        )

    @transaction.atomic  # tout ou rien : une erreur au 40ᵉ membre n'en laisse pas 39 en base
    def handle(self, *args, **options):
        # Garde-fou : en recette ou en production, cette commande effacerait des comptes et
        # créerait des comptes au mot de passe connu de tous.
        if not settings.DEBUG:
            raise CommandError("Commande réservée au développement (DJANGO_DEBUG=1 dans .env).")

        Membre = get_user_model()  # notre modèle Membre (AUTH_USER_MODEL)
        # On les reconnaît à leur adresse seulement : la même adresse est recréée juste après,
        # donc un faux compte oublié ici ferait échouer la création (e-mail déjà pris).
        faux = Membre.objects.filter(email__regex=FAUSSES_ADRESSES)
        supprimes = faux.count()
        faux.delete()  # leurs formations et leurs adresses partent avec eux (CASCADE)

        # Le hachage est volontairement lent (~0,5 s) : on le calcule une seule fois et on
        # donne la même empreinte à tous les faux membres, au lieu d'attendre 10 minutes.
        empreinte = make_password(settings.MOT_DE_PASSE_DONNEES_DEV)
        sans_mot_de_passe = make_password(None)  # inutilisable : aucun mot de passe n'y mène

        # Une seule requête pour chaque référentiel, au lieu d'une par formation créée.
        diplomes = {d.nom: d for d in Diplome.objects.all()}
        sites = {s.nom: s for s in Site.objects.all()}
        membres = generer_membres(options["nombre"], options["graine"])
        adresses = []
        for rang, donnees in enumerate(membres):
            parcours = donnees.pop("parcours")  # ce n'est pas un champ du Membre
            importe = rang % 10 in IMPORTES_SANS_MOT_DE_PASSE
            membre = Membre.objects.create(
                password=sans_mot_de_passe if importe else empreinte,
                statut_inscription=Membre.StatutInscription.VALIDEE,
                compte_active=IMPORTES_SANS_MOT_DE_PASSE.get(rang % 10, True),
                **donnees,
            )
            Formation.objects.bulk_create(
                Formation(
                    membre=membre,
                    diplome=diplomes[etape["diplome"]],
                    site=sites[etape["site"]],
                    promo=etape["promo"],
                )
                for etape in parcours
            )
            # La connexion (django-allauth) demande une adresse vérifiée : sans cette ligne,
            # le faux membre serait renvoyé vers « vérifiez votre adresse ». Un compte importé
            # attend, lui, le lien de sa première connexion pour la vérifier.
            adresses.append(
                EmailAddress(user=membre, email=membre.email, verified=not importe, primary=True)
            )
        EmailAddress.objects.bulk_create(adresses)  # une seule requête pour toutes les adresses

        self.stdout.write(
            self.style.SUCCESS(
                f"{supprimes} faux membres supprimés, {len(membres)} créés. "
                "Mot de passe commun : MOT_DE_PASSE_DONNEES_DEV dans .env."
            )
        )
