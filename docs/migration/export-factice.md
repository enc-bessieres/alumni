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
      "password": "pbkdf2_sha256$1000$…$…", // champ Authentik tel quel ; « !… » = inutilisable
      "origine": "import",                  // import (vague d'avril 2025) ou inscription
      "date_inscription": "2025-04-14T09:12:47Z",
      "derniere_connexion": "2026-02-03T18:30:05Z", // null = jamais connecté
      "statut": "accepte",                  // accepte, en_attente, refuse
      "visible_annuaire": true,
      "categorie": "Alumni",
      "metadata": {
        "civilite": "Mme", "prenom": "Inès", "nom": "Martin", "nom_naissance": null,
        "photo": null,                      // 24 % ont une adresse en .exemple.test
        "localisation": { "commune": "Paris", "departement": "75", "region": "Île-de-France",
                          "pays": "France", "lat": 48.8835, "lng": 2.3219 }
      },
      "experiences": [                      // 28 % en ont de 1 à 3
        { "intitule": "Comptable", "organisation": "Cabinet Exemple Audit", "debut": 2019,
          "fin": null, "poste_actuel": true, "secteur": "Comptabilité", "lieu": "Paris" }
      ],
      "groupes": [
        { "groupe_uuid": "<site>",    "timeline": null },
        { "groupe_uuid": "<diplôme>", "timeline": { "annee": 2019 } } // l'année de promo
      ],
      "liaisons": [{ "fournisseur": "google", "sub": "…" }], // comptes Google ou LinkedIn
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
| Photo | 24 % (une adresse en `.exemple.test` : le site affichera les initiales) | `docs/01`, § 2 et issue #10 |
| Au moins une expérience | 28 % | `docs/01`, § 2 et issue #10 |
| Localisation, avec latitude et longitude | 53 % | `docs/01`, § 2 et issue #10 |
| Deux diplômes | au moins 100 alumni : un premier diplôme, puis un DCG trois ans plus tard | Hypothèse |

> **Le relevé n'est pas cohérent, à vérifier sur l'échantillon :** les catégories font 1222 alors que l'annuaire annonce 1214 membres, et 784 importés + 423 inscrits font 1207. Un membre a peut-être plusieurs catégories. Le factice garde les chiffres par catégorie.

## Les cas difficiles

Ceux de `docs/06-points-durs.md`, § 1. Un membre n'a qu'un seul cas. L'import (#37) devra traiter chacun :

| Cas | Nombre | Comment le reconnaître | Ce que l'import devra faire |
|---|---|---|---|
| Importé jamais activé | 450, dont 40 e-mails morts et 5 sans e-mail | `password` commence par `!`, `derniere_connexion` à `null` | Créer le compte ; le membre l'active par « mot de passe oublié » |
| E-mail mort | 40 | domaine `mort.exemple.test` (convention du factice : le vrai export ne le dira pas) | Le signaler dans le rapport |
| Sans e-mail | 5 | `email` vide | Ne pas l'importer (l'e-mail est obligatoire) et le signaler |
| Google seulement | 30 | `password` inutilisable, une liaison `google` | Garder la liaison pour le rattachement Google |
| LinkedIn seulement | 10 | `password` inutilisable, une liaison `linkedin` | Garder la liaison pour le rattachement LinkedIn |
| Google en plus du mot de passe | 60 | une liaison `google` et un vrai `password` | Garder les deux |
| Doublon | 25 paires | même prénom, nom, diplômes et promos ; deux e-mails ; l'un importé, l'autre inscrit | Les signaler : la fusion est manuelle (Timothée) |
| Homonyme (**pas** un doublon) | 5 paires | même prénom et nom, diplômes différents | Ne **pas** les signaler comme doublons |
| Inscription en attente | 10 | `statut: en_attente`, masqué | Garder le statut |
| Inscription refusée | 5 | `statut: refuse`, masqué | Garder le statut |

## Conventions pour rester factice

- Toutes les adresses sont en **`.test`**, un domaine réservé qui ne peut appartenir à personne : aucun e-mail ne peut partir vers une vraie personne.
- Les comptes qui ont un mot de passe utilisable l'ont tous à `motdepasse-factice`, avec un sel différent. On pourra donc tester la reprise des mots de passe en se connectant avec n'importe quel compte importé.
- Les empreintes sont fabriquées par **le hasher de Django lui-même** (`PBKDF2PasswordHasher`), avec **1 000 itérations** au lieu de 1 000 000, pour générer 1 300 comptes en une seconde. Django lit le nombre d'itérations dans l'empreinte : `check_password` l'accepte, puis Django ré-enregistre l'empreinte au réglage actuel à la première connexion.
- Les employeurs sont visiblement inventés (« Cabinet Exemple Audit », « Banque Fictive du Nord »…).
- Les noms viennent de deux listes de 40 prénoms et 40 noms, combinés sans répétition : seuls les doublons et les homonymes voulus partagent un nom.
