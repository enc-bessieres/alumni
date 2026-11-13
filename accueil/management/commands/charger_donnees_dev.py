"""
Charge les fausses données de développement (issue #10). Jamais de données réelles.

Les sites, niveaux et diplômes sont déjà dans la base : la migration 0002 de `referentiels`
les crée. Cette commande ajoute des faux membres et leur parcours (diplômes et promos).

Elle est rejouable : la relancer remet la base dans le même état. Elle efface d'abord les
faux membres (adresse de la forme prenom.nom.12@exemple.test), puis les recrée. Les comptes
créés à la main (createsuperuser, back-office) ne sont jamais touchés.

Tous les faux membres ont le même mot de passe, connu de l'équipe : la variable
MOT_DE_PASSE_DONNEES_DEV du fichier .env (voir .env.example).
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accueil.fausses_donnees import NOMBRE_PAR_DEFAUT, generer_membres
from referentiels.models import Diplome, Formation, Site

# Les adresses que fabrique fausses_donnees.py, et seulement elles : « admin@exemple.test »
# n'a pas de numéro, il n'est donc jamais effacé.
FAUSSES_ADRESSES = r"^[a-z0-9]+\.[a-z0-9]+\.[0-9]+@exemple\.test$"
MOT_DE_PASSE_PAR_DEFAUT = "motdepasse-factice"


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
        faux = Membre.objects.filter(email__regex=FAUSSES_ADRESSES, is_staff=False)
        supprimes = faux.count()
        faux.delete()  # leurs formations partent avec eux (on_delete=CASCADE)

        # Le hachage est volontairement lent (~0,5 s) : on le calcule une seule fois et on
        # donne la même empreinte à tous les faux membres, au lieu d'attendre 10 minutes.
        mot_de_passe = os.environ.get("MOT_DE_PASSE_DONNEES_DEV", MOT_DE_PASSE_PAR_DEFAUT)
        empreinte = make_password(mot_de_passe)

        # Une seule requête pour chaque référentiel, au lieu d'une par formation créée.
        diplomes = {d.nom: d for d in Diplome.objects.all()}
        sites = {s.nom: s for s in Site.objects.all()}
        membres = generer_membres(options["nombre"], options["graine"])
        for donnees in membres:
            parcours = donnees.pop("parcours")  # ce n'est pas un champ du Membre
            membre = Membre.objects.create(
                password=empreinte,
                statut_inscription=Membre.StatutInscription.VALIDEE,
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

        self.stdout.write(
            self.style.SUCCESS(
                f"{supprimes} faux membres supprimés, {len(membres)} créés. "
                "Mot de passe commun : MOT_DE_PASSE_DONNEES_DEV dans .env."
            )
        )
