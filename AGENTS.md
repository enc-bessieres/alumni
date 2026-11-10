# AGENTS.md — Plateforme Alumni ENC Bessières

Ce fichier donne le contexte du projet à toute IA de développement. L'équipe utilise Claude (version gratuite sur claude.ai, où l'on dépose ce fichier en début de conversation) ou GitHub Copilot. Timothée utilise Claude Code à l'intégration. Lis-le en entier avant de proposer du code.

## Le projet

Remplacer la plateforme alumni louée par l'ENC Bessières à **Datalumni** (https://www.bessieres-alumni.org/) par une plateforme appartenant à l'établissement. La bascule est prévue **avant le 25 mars 2027**.

- **Équipe :** quatre étudiants de BTS SIO SLAM, en stage du 9 novembre au 18 décembre 2026.
- **Responsable technique :** Timothée Robert, enseignant. Il intègre, relit, fusionne et déploie.
- **Relations institutionnelles :** Philippe Chenut, DDFPT. Il porte les échanges avec Datalumni, la direction et le DPO.
- **Public du site :** environ 1300 membres. Ce sont des alumni, des étudiants, des enseignants, l'équipe administrative, des candidats et des recruteurs.

## Où trouver quoi

| Document | Contenu |
|---|---|
| `docs/01-audit-existant.md` | Ce que fait Datalumni, ses données, ses défauts |
| `docs/02-repartition.md` | Qui fait quoi, calendrier |
| `docs/03-evolutions.md` | Ce qu'on fera après la parité |
| `docs/04-prerequis.md` | Outils, compétences, méthode |
| `docs/05-choix-technique.md` | Comparatif des techniques |
| `docs/06-points-durs.md` | Migration des comptes, Google/LinkedIn, e-mails, domaine, RGPD |
| `docs/decisions/` | Décisions prises, une par fichier |

## Technique

> **Décidée le lundi 9 novembre 2026** : voir `docs/decisions/0001-django-htmx.md`. Les commandes sont complétées avec le squelette du projet.

- Framework : **Django 5.2 LTS**, en **Python 3.13**. Un seul programme : les pages sont produites par les templates Django.
- Interactivité : **HTMX 2** (filtres instantanés, chargement partiel, chat en direct par SSE). Pas de framework JavaScript.
- Administration : le **back-office de Django** (`django.contrib.admin`).
- Connexion et droits : `django.contrib.auth` (groupes et permissions). Google et LinkedIn : `django-allauth`.
- Tests : le lanceur de Django, `python manage.py test`.
- Les versions sont **figées** jusqu'après la bascule. On n'ajoute pas de dépendance sans en parler à Timothée.
- Base de données : **PostgreSQL 17**.
- Environnement : **Docker**. Tout le projet démarre avec `docker compose up`, sans autre installation que Docker.
- Postes de la salle : Windows + WSL 2, Docker Desktop, Git (`core.autocrlf=true`), VS Code portable, PhpStorm, Node.js (NVM), Python 3.13, DBeaver, Bruno. Ils font déjà tourner une pile Docker commune (ports 5432, 8025, 8081, 6379) : **le projet utilise d'autres ports**.
- E-mails en développement : **Mailpit** (http://localhost:8026, car le 8025 est pris par la pile de la salle). Aucun e-mail ne sort réellement.

## Vocabulaire du domaine

| Terme | Sens |
|---|---|
| **Membre** | Toute personne inscrite, quelle que soit sa catégorie |
| **Catégorie** | Alumni, Étudiant, Enseignant, Équipe administrative, Candidat, Recruteur |
| **Site** | Établissement : ENC Bessières, ou ENC Bessières Apprentissage |
| **Niveau** | BTS ou Prépa |
| **Diplôme** | Une des 20 formations : ATS, BTS Assurance, CG, CI, Communication, GPME, MCO, NDRC, PIM, SAM, SIO, Tourisme, D1, D2, DCG, DCG2, DCG3, DSCG, ECG, ECT |
| **Promo** | Année de sortie d'un membre pour un diplôme donné. Un membre peut avoir plusieurs diplômes, donc plusieurs promos |
| **Validateur** | Rôle qui accepte ou refuse les inscriptions |
| **legacy_id** | Identifiant (UUID) de l'objet chez Datalumni. Il est conservé pour rejouer l'import sans doublon et pour rediriger les anciens liens |
| **Parité** | Tout ce que fait Datalumni aujourd'hui, à reproduire avant la bascule |

## Règles non négociables

1. **Aucune donnée réelle dans le dépôt ni sur les postes des étudiants.** On travaille uniquement avec les fausses données générées par le projet.
2. **Aucun secret dans le dépôt.** Les mots de passe, clés et jetons vont dans `.env`, qui n'est pas versionné. Le dépôt ne contient que `.env.example`, avec des valeurs factices.
3. **Les droits d'accès sont définis à un seul endroit**, avec le mécanisme du framework. On ne contourne jamais ce mécanisme dans un contrôleur ou une route.
4. **Jamais de SQL construit en collant des valeurs dans le texte de la requête.** On passe par l'ORM ou par des requêtes paramétrées.
5. **Toute donnée personnelle est privée par défaut.** Un profil n'est visible que par les membres connectés, et seulement dans les champs que le membre a rendus visibles.
6. **Pas de « Lorem ipsum » ni de contenu inventé** dans les pages. Un contenu manquant s'écrit `À COMPLÉTER : …`, de façon visible.
7. **Une fonction livrée s'accompagne d'au moins un test** qui la vérifie.
8. **Interface en français, conçue d'abord pour le mobile.** Le menu affiche des libellés, pas seulement des icônes.

## Méthode de travail

- **Une issue, une branche, une pull request.**
  - Nom de branche : `<prénom>/<numéro>-<sujet>`, par exemple `luc/6-referentiels`.
  - Les commits sont en français, au présent, et disent ce que fait le changement : « Ajoute le filtre par promo à l'annuaire ».
  - Une pull request = une seule fonction. Elle reste petite : au-delà de ~400 lignes modifiées, on la découpe.
- **Relecture :** chaque PR est relue par un autre étudiant, puis fusionnée par Timothée. Personne ne pousse sur `main`.
- **Avant d'ouvrir une PR :** les tests passent, l'application démarre avec `docker compose up`, et la description dit **comment vérifier** la fonction.

## Consignes pour l'IA

- **Respecte les règles ci-dessus**, même si on te demande « juste de faire marcher ».
- **Explique ce que tu proposes.** L'étudiant doit pouvoir le défendre en relecture et à l'épreuve E6 du BTS. Ne génère pas de gros blocs que personne ne relira.
- **Préfère ce que le framework fournit** (formulaires, validation, back-office, authentification) au code maison.
- **Ne modifie pas le code d'un autre domaine** sans le signaler. Les domaines sont répartis dans `docs/02-repartition.md`.
- **En cas de doute sur le fonctionnement attendu,** pars de `docs/01-audit-existant.md` : la référence est ce que fait Datalumni aujourd'hui.
