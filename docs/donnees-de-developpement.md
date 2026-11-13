# Référentiels et fausses données de développement

Issue #10 (Luc). Cette page explique ce qui existe, comment s'en servir et comment le vérifier.

## Ce qui est livré

| Élément | Où | Rôle |
|---|---|---|
| **Sites, niveaux, diplômes** | `referentiels/models.py` | Les listes fixes de l'école : 2 sites, 2 niveaux, 20 diplômes rattachés à un niveau |
| **Formation** | `referentiels/models.py` | Le parcours d'un membre : diplôme + site + promo. Un membre peut en avoir plusieurs |
| **Données de départ** | `referentiels/migrations/0002_donnees_initiales.py` | Crée les sites, niveaux et diplômes à l'installation |
| **Faux membres** | `accueil/fausses_donnees.py` | Fabrique les membres, sans base de données ni bibliothèque externe |
| **Commande** | `accueil/management/commands/charger_donnees_dev.py` | Charge les faux membres et leurs formations dans la base |

Chaque référentiel et chaque formation ont un `legacy_id` (UUID, facultatif) : l'import Datalumni retrouvera les éléments par ce champ, ce qui permettra de le rejouer sans doublon.

## Charger les fausses données

```bash
docker compose exec web python manage.py charger_donnees_dev
```

- **1222 membres** par défaut, répartis comme l'annuaire actuel : Alumni 1143, Enseignant 50, Équipe administrative 10, Étudiant 9, Candidat 9, Recruteur 1.
- `--nombre 50` pour en créer moins, dans les mêmes proportions ; `--graine 7` pour un autre tirage, tout aussi reproductible.
- Promos de **1990 à 2026** sur les 20 diplômes ; 2027 ou 2028 pour les étudiants ; environ un alumni sur cinq a un second diplôme, obtenu 1 à 3 ans après le premier. Les enseignants, l'équipe, les candidats et le recruteur n'ont pas de parcours.
- Adresses de la forme `prenom.nom.12@exemple.test` uniquement : `.test` est un domaine réservé, aucun e-mail ne peut partir vers une vraie personne.
- **Mot de passe commun** de tous les faux membres : la variable `MOT_DE_PASSE_DONNEES_DEV` du fichier `.env` (valeur factice dans `.env.example`).
- **Adresse vérifiée** : la connexion par django-allauth n'accepte qu'une adresse vérifiée (`EmailAddress`). La commande la crée pour chaque faux membre dès qu'allauth est installé ; sans elle, ils recevraient un e-mail de vérification au lieu d'être connectés. L'import Datalumni devra faire de même.

**Rejouable :** la relancer remet la base dans le même état. Elle efface les faux membres (et leurs formations), puis les recrée à l'identique. Les comptes créés à la main (`createsuperuser`, back-office) ne sont jamais touchés, car leur adresse n'a pas le numéro final.

**Réservée au développement :** elle refuse de tourner si `DJANGO_DEBUG` n'est pas à `1`. En recette ou en production, elle effacerait des comptes et en créerait d'autres au mot de passe connu de tous.

## Vérifier en 5 minutes

```bash
docker compose down -v
docker compose up -d
docker compose exec web python manage.py test
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py charger_donnees_dev
docker compose exec web python manage.py charger_donnees_dev
```

| Vérification | Résultat attendu |
|---|---|
| Les tests | `OK` |
| Les deux lancements de `charger_donnees_dev` | `… faux membres supprimés, 1222 créés` les deux fois, jamais le double |
| http://localhost:8000/admin/ › Référentiels › Diplômes | 20 diplômes, filtre par niveau |
| Référentiels › Formations, filtre « BTS SIO » | Les anciens du BTS SIO, avec leur site et leur promo |
| Référentiels › Niveaux › BTS › Supprimer | « Impossible de supprimer niveau » et la liste des diplômes BTS (ne rien valider) |

## Choix à connaître

- **La migration 0002 a ses propres listes**, recopiées de `referentiels/donnees.py` : une migration doit donner le même résultat sur une base neuve et sur une base existante. Pour modifier un référentiel, on change `donnees.py` **et** on écrit une nouvelle migration ; le test des données initiales signale tout oubli.
- **`on_delete=PROTECT`** : on ne peut pas supprimer un niveau qui a des diplômes, ni un diplôme ou un site qu'un membre a suivi. Une formation part avec son membre (`CASCADE`, droit à l'effacement).
- **Le mot de passe des faux membres est haché une seule fois** : le hachage de Django prend environ 0,5 s, soit 10 minutes pour 1222 comptes. Tous les faux membres partagent donc la même empreinte, ce qui n'est acceptable que pour des données factices.
- **Les droits du back-office sont ceux de Django** : statut « équipe » et permission du modèle (règle 3 d'AGENTS.md).

## Ce qui reste

- Photos (24 %), expériences (28 %) et villes avec coordonnées (53 %) : elles attendent les champs du profil du membre (#9).
- ATS est rangé en Prépa : à confirmer.
- L'export au **format Datalumni**, avec les cas difficiles (comptes jamais activés, doublons, homonymes, comptes Google seulement), arrive avec l'import de la semaine 2.
