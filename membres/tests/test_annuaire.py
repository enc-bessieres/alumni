from django.conf import settings
from django.db import connection
from django.shortcuts import resolve_url
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from membres.models import Membre
from membres.views import MEMBRES_PAR_PAGE
from referentiels.models import Diplome, Formation, Site

ANNUAIRE = reverse("membres:annuaire")
VALIDEE = Membre.StatutInscription.VALIDEE


def creer(prenom, nom, formations=(), **champs):
    """Un membre validé et visible dans l'annuaire ; `formations` : (diplôme, site, promo)."""
    champs.setdefault("categorie", Membre.Categorie.ALUMNI)
    champs.setdefault("statut_inscription", VALIDEE)
    champs.setdefault("visible_dans_annuaire", True)
    membre = Membre.objects.create_user(
        f"{prenom}.{nom}@exemple.test".lower(),
        "motdepasse-de-test",
        prenom=prenom,
        nom=nom,
        **champs,
    )
    for diplome, site, promo in formations:
        Formation.objects.create(
            membre=membre,
            diplome=Diplome.objects.get(nom=diplome),
            site=Site.objects.get(nom=site),
            promo=promo,
        )
    return membre


class AccesAnnuaireTests(TestCase):
    def test_un_visiteur_est_renvoye_vers_la_connexion(self):
        reponse = self.client.get(ANNUAIRE)

        connexion = resolve_url(settings.LOGIN_URL)
        self.assertRedirects(reponse, f"{connexion}?next={ANNUAIRE}", fetch_redirect_response=False)

    def test_un_membre_valide_voit_l_annuaire(self):
        self.client.force_login(creer("Léa", "Martin"))

        reponse = self.client.get(ANNUAIRE)

        self.assertEqual(reponse.status_code, 200)
        self.assertTemplateUsed(reponse, "membres/annuaire.html")

    def test_un_membre_non_valide_recoit_une_403(self):
        # Par exemple une inscription refusée alors que le membre était déjà connecté.
        for statut in (Membre.StatutInscription.EN_ATTENTE, Membre.StatutInscription.REFUSEE):
            with self.subTest(statut=statut):
                self.client.force_login(creer("Paul", statut, statut_inscription=statut))

                self.assertEqual(self.client.get(ANNUAIRE).status_code, 403)

    def test_le_menu_mene_a_l_annuaire(self):
        self.client.force_login(creer("Léa", "Martin"))

        reponse = self.client.get(ANNUAIRE)

        self.assertContains(reponse, f'<a href="{ANNUAIRE}" aria-current="page">Annuaire</a>')


class AnnuaireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lecteur = creer("Ines", "Lecteur", visible_dans_annuaire=False)
        cls.lea = creer(
            "Léa",
            "Martin",
            [("BTS SIO", "ENC Bessières", 2012), ("DCG", "ENC Bessières Apprentissage", 2020)],
        )
        cls.hugo = creer(
            "Hugo",
            "Lefèvre",
            [("BTS SIO", "ENC Bessières", 2020)],
            categorie=Membre.Categorie.ETUDIANT,
        )
        cls.zoe = creer("Zoé", "Dupont", categorie=Membre.Categorie.ENSEIGNANT)

    def setUp(self):
        self.client.force_login(self.lecteur)

    def membres_affiches(self, **filtres):
        reponse = self.client.get(ANNUAIRE, filtres)
        return {str(membre) for membre in reponse.context["page"].object_list}

    def test_affiche_seulement_les_membres_visibles_actifs_et_valides(self):
        creer("Masqué", "Choix", visible_dans_annuaire=False)
        creer("Ancien", "Inactif", is_active=False)
        creer("Pas", "Encore", statut_inscription=Membre.StatutInscription.EN_ATTENTE)

        self.assertEqual(self.membres_affiches(), {"Léa Martin", "Hugo Lefèvre", "Zoé Dupont"})

    def test_n_affiche_jamais_l_adresse_e_mail(self):
        reponse = self.client.get(ANNUAIRE)

        self.assertNotContains(reponse, "@exemple.test")

    def test_affiche_les_diplomes_avec_site_et_promo(self):
        reponse = self.client.get(ANNUAIRE, {"q": "lea"})

        self.assertContains(reponse, "BTS SIO, promo 2012 — ENC Bessières")
        self.assertContains(reponse, "DCG, promo 2020 — ENC Bessières Apprentissage")

    def test_la_recherche_ignore_les_accents_et_les_majuscules(self):
        for recherche in ("lea", "LÉA", "lefevre", "Lefèvre"):
            with self.subTest(recherche=recherche):
                self.assertEqual(len(self.membres_affiches(q=recherche)), 1)

    def test_la_recherche_par_prenom_et_nom(self):
        self.assertEqual(self.membres_affiches(q="lea martin"), {"Léa Martin"})
        self.assertEqual(self.membres_affiches(q="lea dupont"), set())

    def test_filtre_par_categorie(self):
        self.assertEqual(self.membres_affiches(categorie="etudiant"), {"Hugo Lefèvre"})

    def test_filtre_par_diplome_site_et_promo(self):
        sio = Diplome.objects.get(nom="BTS SIO").pk
        apprentissage = Site.objects.get(nom="ENC Bessières Apprentissage").pk

        self.assertEqual(self.membres_affiches(diplome=sio), {"Léa Martin", "Hugo Lefèvre"})
        self.assertEqual(self.membres_affiches(site=apprentissage), {"Léa Martin"})
        self.assertEqual(self.membres_affiches(promo=2020), {"Léa Martin", "Hugo Lefèvre"})

    def test_diplome_et_promo_d_une_meme_formation(self):
        # Léa a un BTS SIO en 2012 et un DCG en 2020 : elle n'est pas « BTS SIO 2020 ».
        sio = Diplome.objects.get(nom="BTS SIO").pk

        self.assertEqual(self.membres_affiches(diplome=sio, promo=2020), {"Hugo Lefèvre"})

    def test_deux_filtres_se_combinent(self):
        sio = Diplome.objects.get(nom="BTS SIO").pk

        self.assertEqual(self.membres_affiches(diplome=sio, categorie="alumni"), {"Léa Martin"})

    def test_une_valeur_invalide_est_ignoree(self):
        self.assertEqual(len(self.membres_affiches(promo="abc", site="999")), 3)

    def test_aucun_resultat(self):
        reponse = self.client.get(ANNUAIRE, {"q": "personne"})

        self.assertContains(reponse, "Aucun membre ne correspond à votre recherche.")


class PaginationAnnuaireTests(TestCase):
    def setUp(self):
        self.client.force_login(creer("Ines", "Lecteur", visible_dans_annuaire=False))

    def test_la_liste_est_paginee_et_garde_les_filtres(self):
        for numero in range(MEMBRES_PAR_PAGE + 1):
            creer("Alumni", f"Numero{numero:02}")

        reponse = self.client.get(ANNUAIRE, {"q": "alumni"})

        self.assertEqual(len(reponse.context["page"].object_list), MEMBRES_PAR_PAGE)
        self.assertContains(reponse, 'href="?q=alumni&amp;page=2"')
        page_2 = self.client.get(ANNUAIRE, {"q": "alumni", "page": 2})
        self.assertEqual(len(page_2.context["page"].object_list), 1)

    def test_le_nombre_de_requetes_ne_depend_pas_du_nombre_de_membres(self):
        # Les formations sont chargées en une fois pour toute la page (prefetch_related).
        def requetes():
            with CaptureQueriesContext(connection) as capture:
                self.client.get(ANNUAIRE)
            return len(capture)

        creer("Un", "Seul", [("BTS SIO", "ENC Bessières", 2020)])
        avec_un_membre = requetes()
        for numero in range(10):
            creer("Autre", f"Membre{numero}", [("DCG", "ENC Bessières", 2015)])

        self.assertEqual(requetes(), avec_un_membre)


class HtmxAnnuaireTests(TestCase):
    def setUp(self):
        self.client.force_login(creer("Léa", "Martin"))

    def test_htmx_ne_recoit_que_la_liste(self):
        reponse = self.client.get(ANNUAIRE, {"q": "lea"}, headers={"HX-Request": "true"})

        self.assertTemplateUsed(reponse, "membres/_resultats.html")
        self.assertTemplateNotUsed(reponse, "membres/annuaire.html")
        self.assertIn("HX-Request", reponse["Vary"])

    def test_le_retour_arriere_recoit_la_page_entiere(self):
        entetes = {"HX-Request": "true", "HX-History-Restore-Request": "true"}

        reponse = self.client.get(ANNUAIRE, headers=entetes)

        self.assertTemplateUsed(reponse, "membres/annuaire.html")
