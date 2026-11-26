# Import de l'annuaire Datalumni

Issue #84 (Luc). La commande lit le `directory.csv` de Datalumni, décrit dans [export-reel.md](export-reel.md), et crée un compte par ligne. Pour s'entraîner, on utilise l'export factice, au même format ([export-factice.md](export-factice.md)).

```bash
docker compose exec web python manage.py generer_export_factice
docker compose exec web python manage.py importer_datalumni exports/datalumni-factice-directory.csv
```

→ « 6138 membres créés, 0 mis à jour, 0 ignorés, en … s. », puis la liste des comptes ignorés.

Le vrai fichier ne s'importe que sur le poste de la personne autorisée, depuis `sources/` (décision 0006). Ni ses lignes ni la liste des comptes ignorés ne se copient dans une issue, une PR, Slack ou une IA : on cite seulement des nombres, ou un identifiant Datalumni.

## Rejouable, tout ou rien

- Un membre est retrouvé par son identifiant Datalumni (`user_id` → `legacy_id`) : relancer l'import **ne crée pas de doublon**. Il remet à jour ce que l'export contient (nom, catégorie, civilité, visibilité, dernière connexion).
- **Jamais écrasé par une relance** : le mot de passe que le membre a défini sur le nouveau site, et le statut de son inscription.
- Une erreur au milieu annule tout : la base n'est jamais à moitié importée.

## Correspondance des colonnes

| `directory.csv` | Nouveau site | Règle |
|---|---|---|
| `user_id` | `legacy_id` | Retrouve le membre à chaque relance |
| `email` | `email`, et l'adresse de django-allauth | En minuscules. Adresse **non vérifiée** : elle le sera quand le membre définira son mot de passe par le lien reçu (#85) |
| — | Mot de passe | **Aucun mot de passe utilisable** : Datalumni ne les fournit pas |
| — | `statut_inscription` | « Validée » : un compte activé chez Datalumni est considéré comme validé |
| `first_name`, `last_name`, `birth_name` | `prenom`, `nom`, `nom_de_naissance` | **Gardés tels quels**, majuscules comprises (à confirmer par M. Robert) |
| `civility` | `civilite` | `Mme.` et `Madame` → madame ; `M.` et `Monsieur` → monsieur ; `Non renseigné` → vide |
| `category` | `categorie` | Deux catégories : **la première est gardée** (à confirmer par M. Robert) |
| `visibility_directory` | `visible_dans_annuaire` | Toujours `True` chez Datalumni ; une case vide aussi |
| `import_date`, sinon `account_activation_date` | `cree_le` | |
| `last_login` | `last_login` | |

**Pas encore importés :**
- `account_status` : il attend le champ `compte_active` (PR d'Alex) ;
- `campus`, `degree`, `promotion_year` : prochaine PR (diplômes et promos) ;
- `location`, `phone`, poste actuel, secteur, préférences, mentorat : ils attendent les champs du profil.

## Les comptes ignorés

Ils ne sont pas créés, et la commande les liste à la fin, **par leur identifiant Datalumni seulement**.

| Cas | Pourquoi |
|---|---|
| Pas d'adresse e-mail | Elle est obligatoire pour se connecter |
| Catégorie inconnue | Le format réel a peut-être changé : à vérifier |
| Adresse déjà utilisée par un autre compte | On ne touche pas au compte existant. À trancher à la main : le rattacher à Datalumni, ou laisser la personne choisir |

Les comptes sans catégorie ou sans nom sont importés. Le rapport des cas à vérifier (sans catégorie, sans nom, plusieurs catégories, homonymes) arrive dans la PR suivante.
