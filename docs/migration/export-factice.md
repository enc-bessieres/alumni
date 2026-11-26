# Export factice de l'annuaire Datalumni

Issues #36 et #84 (Luc). L'export factice est un **faux `directory.csv`** : le même fichier que l'export réel de l'annuaire, décrit dans [export-reel.md](export-reel.md), mais rempli de personnes inventées (règle 1 d'AGENTS.md).

Les tests, l'intégration continue, les démos et la mesure de durée de l'import s'appuient **sur lui, jamais sur les fichiers réels** (décision 0006).

```bash
docker compose exec web python manage.py generer_export_factice             # écrit exports/datalumni-factice-directory.csv
docker compose exec web python manage.py generer_export_factice --graine 7  # un autre export, tout aussi reproductible
```

Le dossier `exports/` n'est pas versionné (`.gitignore`). Même graine, même fichier, au caractère près : deux imports à blanc sur le même export sont comparables.

Ne pas confondre avec `charger_donnees_dev`, qui remplit directement la base pour travailler en local. L'export factice est un **fichier**, que l'import lira.

## Ce qui est identique au vrai export

- **Le format** : les 28 colonnes, dans le même ordre ; UTF-8 avec BOM ; virgules ; une ligne d'en-tête ; `True` et `False` en toutes lettres ; une case vide quand Datalumni n'a rien.
- **Les volumes, colonne par colonne** : 6138 comptes, dont 1233 activés, avec la répartition par catégorie, et le nombre de cases remplies de chaque colonne. C'est le tableau de [export-reel.md](export-reel.md), vérifié par `datalumni/tests/test_export_factice.py`.
- **Les cas à traiter par l'import** :
  - 4 comptes sans nom ;
  - 6036 noms en majuscules ;
  - 5 écritures de civilité ;
  - 12 doubles catégories, 52 doubles sites et 121 comptes à plusieurs diplômes pour une seule promo, séparés par ` / ` ;
  - 437 comptes sans diplôme ;
  - promos de 1963 à 2029 ;
  - 455 comptes inscrits seuls (`import_date` vide) ;
  - **128 groupes d'homonymes** (259 comptes).
- **Les listes** : les 26 secteurs de `business_sector`, et les diplômes et sites du référentiel (`referentiels/donnees.py`).

## Ce qui est inventé

| Colonne | Dans l'export factice |
|---|---|
| `first_name`, `last_name`, `birth_name` | Des prénoms et des noms courants, combinés au hasard |
| `email` | `prenom.nom.N@exemple.test`, et `@enc-bessieres.exemple.test` pour imiter les 2048 adresses de l'école : jamais un vrai domaine |
| `phone` | `+3363998…` : la plage que l'ARCEP réserve à la fiction |
| `location`, `current_position`, `current_company` | Quelques villes, des postes et des entreprises « Exemple » |
| Les dates | Tirées entre l'ouverture de Datalumni (26 mars 2025) et le relevé (25 novembre 2026), avec les deux vagues d'import (avril et octobre 2025) |

**Hypothèses à vérifier sur le vrai fichier** (par la personne qui a accès à `sources/`, sans copier de ligne) :
- le format exact de `import_date` : ici, une date ISO avec fuseau, comme `last_login` ;
- l'ordre des colonnes : ici, celui du tableau de `export-reel.md`.

Pas d'export factice des offres, des candidatures ni des mentorats : leurs fichiers réels ont trop peu de lignes pour être importés (voir [export-reel.md](export-reel.md)).
