# Import des membres de Datalumni

Issue #37 (Luc). La commande lit l'export de Datalumni (pour l'instant l'export factice, voir [export-factice.md](export-factice.md)) et crée un compte par membre. Chaque membre se connecte ensuite **avec son mot de passe habituel**, sans se réinscrire.

```bash
docker compose exec web python manage.py generer_export_factice
docker compose exec web python manage.py importer_datalumni exports/datalumni-factice.json
```

→ « 1300 membres créés, 0 mis à jour, 0 ignorés. »

## Rejouable, tout ou rien

- Un membre est retrouvé par son identifiant Datalumni (`legacy_id`) : relancer l'import **ne crée pas de doublon**, il remet les comptes à jour.
- Une erreur au milieu annule tout : la base n'est jamais à moitié importée.
- **À ne relancer qu'avant la bascule** : l'import remet les comptes dans l'état de Datalumni (mot de passe, visibilité, statut). Ce qu'un membre aurait changé sur le nouveau site serait écrasé.

## Correspondance des champs

| Export Datalumni | Nouveau site | Règle |
|---|---|---|
| `uuid` | `legacy_id` | Retrouve le membre à chaque relance |
| `email` | `email` | En minuscules |
| `email_verifie` | Adresse django-allauth (`EmailAddress`) | Vérifiée ou non, comme chez Datalumni |
| `password` | `password`, tel quel | Même format que Django (`pbkdf2_sha256`) : l'ancien mot de passe marche. Django ré-enregistre l'empreinte à la première connexion |
| `metadata.civilite` | `civilite` | `M.` → monsieur, `Mme` → madame |
| `metadata.prenom`, `nom`, `nom_naissance` | `prenom`, `nom`, `nom_de_naissance` | |
| `categorie` | `categorie` | « Équipe administrative » → administratif… |
| `statut` | `statut_inscription` | `accepte` → validée, `en_attente`, `refuse` → refusée |
| `visible_annuaire` | `visible_dans_annuaire` | Sinon l'annuaire serait vide (faux par défaut, #41) |
| `date_inscription`, `derniere_connexion` | `cree_le`, `last_login` | |

Pas encore importés : diplômes et promos (#38), photos, expériences et villes (champs du profil à venir), liaisons Google et LinkedIn (applications de l'ENC à venir).

## Les comptes ignorés

Ils ne sont pas créés, et la commande les liste à la fin, **par leur identifiant Datalumni seulement** : sur le vrai export, un nom ou un e-mail n'a rien à faire dans un terminal.

| Cas | Pourquoi |
|---|---|
| Pas d'adresse e-mail | Elle est obligatoire pour se connecter |
| Catégorie ou statut inconnu | Le format réel diffère peut-être du format supposé : à vérifier |
| Adresse déjà utilisée par un autre compte | On ne touche pas au compte existant. **À trancher** : le rattacher à Datalumni, ou laisser la personne choisir ? |

Un compte jamais activé (mot de passe qui commence par `!`) est importé : son propriétaire l'active par « mot de passe oublié ».

Le rapport détaillé des cas à traiter à la main (doublons, homonymes) viendra dans la seconde PR de l'issue #37.
