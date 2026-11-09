# Choix technique

> **Décision du lundi 9 novembre 2026 : Django + HTMX** (option C). Voir [decisions/0001-django-htmx.md](decisions/0001-django-htmx.md). La comparaison ci-dessous est conservée pour garder la trace du raisonnement.

L'équipe va travailler 6 semaines sur ce projet (stage du 9 novembre au 18 décembre 2026), et **la décision se prend le lundi 9 à 17 h**. La technique doit lui donner envie, et doit produire le plus possible dans ce délai. Ce document compare quatre options pour en discuter avec les étudiants.

## Le choix de l'an dernier

**C'était un bon choix.** Next.js + Payload est une technique moderne et cohérente, et elle reste une option sérieuse. Ce qui change cette année, ce sont les contraintes : mise en production, reprise des données, maintenance après le départ de l'équipe. Ce document compare les options à l'aune de ces contraintes.

## Ce qui fait vraiment la différence ici

1. **Six semaines.** Ce que le framework fournit tout fait vaut de l'or : back-office d'administration, connexion, gestion des droits, migrations de base.
2. **Les mots de passe Datalumni.** Datalumni gère ses comptes avec Authentik, un logiciel écrit en **Django**. Les mots de passe y sont donc stockés au format Django (`pbkdf2_sha256$…`). Django les relit **sans une ligne de code**. Les autres options demandent d'écrire ce vérificateur.
3. **La maintenance après juin 2027.** Elle reviendra à Timothée et aux promos suivantes. Une version maintenue plusieurs années (LTS) évite de tout mettre à jour chaque rentrée.
4. **Une ou deux bases de code.** Un front séparé de l'API double les langages, les déploiements et les sources de bugs.

## Les quatre options

### A. Next.js + Payload — reprendre leur technique, dans un dépôt neuf

Le site et l'administration sont écrits en TypeScript, avec React pour les écrans.

| Pour | Contre |
|---|---|
| **Axel, Luc et Steeve l'ont déjà pratiquée** sur le prototype ; une partie de leurs écrans se reprend, dont le **chat en direct** | Les versions changent vite : Next.js 14, 15 puis 16 en deux ans, Payload 2 puis 3 |
| Payload fournit le back-office, la connexion et les migrations | Payload a une communauté encore petite, donc moins de réponses toutes prêtes |
| Interfaces riches (carte, messagerie) faciles en React | Marie Dominique devra se former à React et TypeScript |
| Bonne base pour une PWA | Le vérificateur de mots de passe Django est à écrire (~30 lignes) |
| Technique « tendance », motivante | Peu enseignée en BTS SIO, donc la reprise par les promos suivantes est plus difficile |

### B. Nuxt + Django REST — sans doute la même technique que Datalumni

Il y a deux applications : un front en Vue (Nuxt) et une API en Python (Django REST Framework).

| Pour | Contre |
|---|---|
| Probablement la même architecture que la plateforme actuelle (Datalumni ne l’a pas confirmé ; seule sa connexion, Authentik, est en Django de façon certaine) | **Deux bases de code**, deux langages, deux déploiements, et une connexion à faire passer entre les deux |
| Mots de passe Datalumni relus nativement par Django | En 6 semaines, l'API et le front se partagent le temps : à 4, on livre moins |
| Back-office Django gratuit | Nuxt a lui aussi changé de version majeure (3 puis 4 en 2025) |
| Python apprécié des étudiants ; Vue plus simple que React | Reprendre « la même technique » n'apporte rien en soi : on ne récupère pas le code de Datalumni, seulement ses données |
| Une API toute prête si on veut une application mobile native plus tard | |

### C. Django seul + HTMX — un seul programme Python

Django produit les pages lui-même (templates). HTMX ajoute l'interactivité (filtres instantanés, chargement partiel) sans écrire de JavaScript.

| Pour | Contre |
|---|---|
| **Mots de passe Datalumni relus nativement**, sans code | Moins « tendance » qu'un front JavaScript, il faut le présenter comme un choix d'efficacité |
| **Back-office Django** gratuit : comptes, rôles, contenus, validations, sans écrire d'écran | Interfaces très dynamiques (messagerie en temps réel) plus laborieuses : il faut Django Channels, ou se contenter d'un rafraîchissement régulier |
| **Une seule base de code, un seul langage (Python)** | HTMX est nouveau pour les étudiants, mais il s'apprend en une journée |
| Django 5.2 **LTS**, maintenu jusqu'en avril 2028 ; un framework stable depuis 20 ans | |
| Python apprécié des étudiants ; énormément d'aide en ligne et de très bonnes réponses des IA | |
| PWA possible (manifeste + *service worker*), et l'API pour une app native s'ajoute plus tard avec Django REST Framework | |

### D. Symfony + Twig/Turbo — la technique du programme SLAM

Il n'y a qu'un seul programme, en PHP.

| Pour | Contre |
|---|---|
| Au programme du BTS SIO SLAM | **Timothée n'en est pas spécialiste**, alors que c'est lui qui intègre et déploie |
| Symfony 7.4 **LTS**, maintenu jusqu'en 2029 | Vérificateur de mots de passe Django à écrire (~20 lignes) |
| Droits centralisés (Security, voters), migrations Doctrine, back-office EasyAdmin | Plus de configuration que Django pour démarrer |
| Une seule base de code | Moins motivant si les étudiants préfèrent Python |

## Comparatif

Légende : ++ très favorable · + favorable · ~ neutre · − défavorable.

| Critère | A. Next + Payload | B. Nuxt + Django | C. Django + HTMX | D. Symfony |
|---|:-:|:-:|:-:|:-:|
| Fourni tout fait (admin, connexion, migrations) | + | + | ++ | + |
| Reprise des mots de passe Datalumni | − | ++ | ++ | + |
| Bases de code | 1 | **2** | 1 | 1 |
| Rendement en 6 semaines à 4 | ++ | − | + | + |
| Stabilité, maintenance après juin | − | ~ | ++ | ++ |
| Intégration par Timothée | ? | − | ? | − |
| Interfaces riches (carte, messagerie) | ++ | ++ | + | + |
| Version mobile (PWA) | ++ | ++ | + | + |
| Envie de l'équipe | à demander | à demander | à demander | à demander |

Les « ? » dépendent de ce que Timothée maîtrise déjà : Node.js ou Python.

## Décision

**C. Django + HTMX.** Les mots de passe Datalumni passent sans code, le back-office et la connexion sont fournis, il n'y a qu'un langage et qu'une base de code, et Django 5.2 est maintenu jusqu'en avril 2028.

Le prototype de 2026 reste la référence fonctionnelle : on reprend ses écrans et ses parcours, réécrits en Django. Son chat en direct garde la même technique (SSE), servie par Django.

Le détail est dans [decisions/0001-django-htmx.md](decisions/0001-django-htmx.md).

## Comment animer la discussion

1. Présenter les quatre options et ce tableau, sans donner la recommandation d'abord. Demander à Axel, Luc et Steeve ce qu'ils retiennent de leur expérience avec Next.js + Payload : ce qui a bien marché, ce qui les a gênés.
2. Demander à chacun ce qu'il connaît (React, Vue, Python/Django, Symfony) et ce qu'il a envie d'apprendre.
3. Faire faire à chacun, en 2 heures, la même mini-tâche dans l'option qui le tente : une page « liste des membres filtrée par promo » avec sa page d'administration. Le comparatif devient concret, et le choix devient le leur.
4. Trancher ensemble, et noter la décision et ses raisons dans `docs/`.
