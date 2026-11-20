# Export factice au format Datalumni

Issue #36 (Luc). Tant que l'échantillon de Datalumni n'est pas arrivé, l'import se construit sur un **export factice** : un fichier JSON qui a la forme supposée du vrai export, rempli de personnes inventées (règle 1 d'AGENTS.md).

Ne pas confondre avec `charger_donnees_dev` : cette commande remplit directement la base pour travailler en local. L'export factice est un **fichier**, que l'import lira.

```bash
docker compose exec web python manage.py generer_export_factice             # écrit exports/datalumni-factice.json
docker compose exec web python manage.py generer_export_factice --graine 7  # un autre export, tout aussi reproductible
```

Le dossier `exports/` n'est pas versionné (`.gitignore`). Même graine, même fichier, au caractère près : deux migrations à blanc sur le même export sont comparables.

## Un format supposé

> **Le format est une hypothèse.** Il est déduit de l'API membre relevée dans `docs/01-audit-existant.md` (§ 2) et de la liste des demandes de `docs/06-points-durs.md` (§ 8). Quand l'échantillon arrive, on adapte `datalumni/export_factice.py` et la lecture de l'import, et rien d'autre.

```jsonc
{
  "format": "datalumni-factice/1",
  "groupes": [
    { "uuid": "…", "type": "site",    "nom": "ENC Bessières", "parent_uuid": null },
    { "uuid": "…", "type": "niveau",  "nom": "BTS",           "parent_uuid": null },
    { "uuid": "…", "type": "diplome", "nom": "BTS SIO",       "parent_uuid": "<uuid du niveau BTS>" }
  ],
  "membres": [
    {
      "uuid": "…",                          // deviendra legacy_id
      "email": "ines.martin.12@exemple.test",
      "email_verifie": true,
      "password": "pbkdf2_sha256$1000$…$…", // champ Authentik tel quel
      "origine": "import",                  // import (vague d'avril 2025) ou inscription
      "date_inscription": "2025-04-14T09:12:47Z",
      "derniere_connexion": "2026-02-03T18:30:05Z",
      "statut": "accepte",                  // accepte, en_attente, refuse
      "visible_annuaire": true,
      "categorie": "Alumni",
      "metadata": {
        "civilite": "Mme", "prenom": "Inès", "nom": "Martin", "nom_naissance": null,
        "photo": null,
        "localisation": { "commune": "Paris", "departement": "75", "region": "Île-de-France",
                          "pays": "France", "lat": 48.8835, "lng": 2.3219 }
      },
      "experiences": [
        { "intitule": "Comptable", "organisation": "Cabinet Exemple Audit", "debut": 2019,
          "fin": null, "poste_actuel": true, "secteur": "Comptabilité", "lieu": "Paris" }
      ],
      "groupes": [
        { "groupe_uuid": "<site>",    "timeline": null },
        { "groupe_uuid": "<diplôme>", "timeline": { "annee": 2019 } } // l'année de promo
      ],
      "liaisons": [],                       // comptes Google ou LinkedIn rattachés
      "consentements": { "cgu_acceptees_le": "2025-04-14T09:12:47Z", "newsletter": false }
    }
  ]
}
```

Pas encore générés : compétences, mentorat, contenus, messages, fichiers. On les ajoutera avec l'import qui en a besoin.

## Ce que contient l'export par défaut

Les volumes reprennent l'annuaire relevé le 8 novembre 2026 :

| Élément | Nombre | Source |
|---|---|---|
| Membres visibles dans l'annuaire | 1222 (Alumni 1143, Enseignant 50, Équipe administrative 10, Étudiant 9, Candidat 9, Recruteur 1) | `docs/01`, § 2 |
| Membres masqués de l'annuaire | 78 | Hypothèse, pour arriver à « environ 1300 » |
| Comptes importés en avril 2025 | 784 (le reste s'est inscrit seul) | `docs/01`, § 2 |
| Promos | de 1990 à 2026 pour les alumni, 2027 ou 2028 pour les étudiants, sur les 20 diplômes | issue #10 |
| Deux diplômes | 120 alumni : un premier diplôme, puis un DCG trois ans plus tard | Hypothèse |

> **Le relevé n'est pas cohérent, à vérifier sur l'échantillon :** les catégories font 1222 alors que l'annuaire annonce 1214 membres, et 784 importés + 423 inscrits font 1207. Un membre a peut-être plusieurs catégories. Le factice garde les chiffres par catégorie.

Arrivent dans la seconde PR de l'issue #36 :

- les **profils peu remplis** de la plateforme actuelle : 24 % de photos, 28 % d'expériences, 53 % de villes avec coordonnées (pour l'instant, `photo`, `localisation` et `experiences` sont vides) ;
- les **cas difficiles** de `docs/06-points-durs.md` (§ 1) : comptes jamais activés, sans e-mail, doublons, homonymes, comptes Google ou LinkedIn seulement.

## Conventions pour rester factice

- Toutes les adresses sont en **`.test`**, un domaine réservé qui ne peut appartenir à personne : aucun e-mail ne peut partir vers une vraie personne.
- Tous les comptes ont le mot de passe `motdepasse-factice`, avec un sel différent. On pourra donc tester la reprise des mots de passe en se connectant avec n'importe quel compte importé.
- Les empreintes sont fabriquées par **le hasher de Django lui-même** (`PBKDF2PasswordHasher`), avec **1 000 itérations** au lieu de 1 000 000, pour générer 1 300 comptes en une seconde. Django lit le nombre d'itérations dans l'empreinte : `check_password` l'accepte, puis Django ré-enregistre l'empreinte au réglage actuel à la première connexion.
- Les noms viennent de deux listes de 40 prénoms et 40 noms, combinés sans répétition : deux membres ne portent jamais le même nom par hasard.
