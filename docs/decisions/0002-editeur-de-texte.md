# 0001 — Django + HTMX

**Date :** lundi 9 novembre 2026
**Statut :** décidée

## Contexte

Quatre options ont été comparées dans [05-choix-technique.md](../05-choix-technique.md) : Next.js + Payload, Nuxt + Django REST, Django + HTMX, Symfony. Le site doit être en production en mars 2027, puis maintenu par Timothée et les promos suivantes.

## Décision

**Django + HTMX**, dans un seul programme Python, avec PostgreSQL et Docker.

| Élément | Version |
|---|---|
| Python | 3.13 |
| Django | 5.2 LTS (maintenu jusqu'en avril 2028) |
| PostgreSQL | 17 |
| HTMX | 2 |

Les versions restent figées jusqu'après la bascule.

## Raisons

1. **Les mots de passe Datalumni passent sans code.** Ils sont au format Django (`pbkdf2_sha256$…`) : on les copie dans le champ `password` et Django les vérifie au login.
2. **Le framework fournit l'essentiel :** back-office d'administration, connexion, droits, formulaires, migrations. En 6 semaines, c'est ce qui permet d'atteindre la parité.
3. **Un seul langage et une seule base de code**, qu'on déploie en un seul conteneur.
4. **La maintenance :** une version LTS, un framework stable depuis 20 ans, facile à reprendre par les promos suivantes.

## Ce que ça implique

- **Le prototype de 2026** (Next.js + Payload) n'est pas repris tel quel. On reprend ses écrans, ses parcours et ses choix d'interface, et on les réécrit en Django. Axel, Luc et Steeve connaissent déjà ces fonctions : ils savent ce qu'il faut construire.
- **Le chat en direct** garde la technique du prototype : des *Server-Sent Events* (SSE), une connexion que le serveur garde ouverte pour envoyer chaque nouveau message. Django les sert avec une vue asynchrone, sous un serveur ASGI (Uvicorn). PostgreSQL signale chaque nouveau message (`LISTEN/NOTIFY`), ce qui évite d'interroger la base en boucle. HTMX a une extension SSE pour afficher les messages. Il n'y a pas de Redis ni de Django Channels à installer.
- **Google et LinkedIn** passent par `django-allauth`, en semaine 2.
- **Les tests** utilisent le lanceur de Django (`manage.py test`).
