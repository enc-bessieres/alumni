# Prérequis et organisation technique

## 1. Le projet de 2026 : notre point de départ

En un stage de première année, **Axel, Luc et Steeve** ont reproduit l'essentiel des fonctions du site dans [Awerox/Alumni_Clone](https://github.com/Awerox/Alumni_Clone) : profils, annuaire avec carte, groupes, événements, blog, offres, messagerie, connexion Google et LinkedIn. C'est un travail remarquable, et c'est lui qui rend le projet de cette année crédible. Tous les trois font partie de l'équipe cette année.

Une mise en production demande des choses qu'on n'attend pas d'un stage de première année :

| Point | Ce qu'il reste à faire |
|---|---|
| Installation | Un README et une configuration qui permettent à un nouveau venu de démarrer seul |
| Droits d'accès | Réserver les profils (téléphone, rémunération) aux seuls membres autorisés, puisque le site sera public avec de vraies données |
| Robustesse | Passer par l'ORM plutôt que par du SQL écrit à la main ; ajouter des tests ; réunir les deux branches |
| Hébergement | Le code a été adapté aux offres gratuites (Vercel, Neon) ; la production de l'ENC sera hébergée autrement |

On ouvre donc un dépôt neuf, où ils reprennent leurs écrans et leurs parcours. Si l'équipe reste sur Next.js + Payload, comme je le recommande, une partie de leur code pourra être reprise directement.

## 2. La technique : à trancher avec l'équipe

Quatre options sont comparées dans [05-choix-technique.md](05-choix-technique.md) :

- A. Next.js + Payload ;
- B. Nuxt + Django ;
- C. Django + HTMX ;
- D. Symfony.

Ma recommandation est **Next.js + Payload**, que trois des quatre étudiants ont déjà pratiquée, dans un dépôt neuf. La décision se prend avec eux.

## 3. Prérequis : le strict nécessaire

**Déjà sur les postes de la salle**, rien à installer : Docker Desktop, Git, VS Code, PhpStorm, Node.js, Python, DBeaver, Bruno.

**À avoir :**

| Quoi | Pourquoi |
|---|---|
| Son compte GitHub (chacun en a déjà un), avec authentification à deux facteurs | Contribuer au dépôt de l'équipe |
| Slack | Échanger au quotidien |
| Un compte Claude gratuit (claude.ai) | L'assistant IA de l'équipe, en y déposant `AGENTS.md` en début de conversation |

**Facultatif :** le GitHub Student Developer Pack, gratuit, qui donne GitHub Copilot dans VS Code. Aucun abonnement payant n'est demandé.

**Côté établissement :**
- **Philippe Chenut** (DDFPT) : accès administrateur Datalumni, demande d'export, propriété du domaine, administrateur de la page LinkedIn de l'école.
- **Philippe :** donner son accord à la création d'un **espace GitHub au nom de l'ENC** (une « organisation » `enc-bessieres`, gratuite), et en devenir le second propriétaire, pour que le projet ne dépende pas d'une seule personne.
- **Timothée :** créer cette organisation et demander les avantages GitHub Education.

## 4. Le dépôt et les adresses

**Le dépôt de travail :**
- On crée un **nouveau dépôt** `enc-bessieres/alumni` dans l'organisation de l'école. Le prototype est transféré dans l'organisation, puis archivé : GitHub redirige automatiquement l'ancienne adresse.
- On le garde **public**. C'est sans risque à deux conditions : **aucune donnée réelle** et **aucun secret** dans le dépôt. C'est même un atout :
  - les protections de branche sont gratuites sur un dépôt public ;
  - les étudiants valorisent ce projet dans leur portfolio pour l'épreuve E6 du BTS.

**L'adresse du site :** on garde **bessieres-alumni.org**, ce qui préserve les liens partagés, les marque-pages et les e-mails déjà envoyés. Il reste deux points à régler :

1. **Le domaine expire le 25 mars 2027.** Il a été enregistré chez OVH le 25 mars 2025, la veille du lancement Datalumni.
   - Il faut savoir **à qui appartient le compte OVH** : à l'ENC ou à Datalumni ?
   - Si c'est à Datalumni, il faut demander le transfert **maintenant**.
   - Dans tous les cas, il faut le renouveler avant mars.
2. **Les environnements :**

   | Environnement | Adresse | Accès | Données |
   |---|---|---|---|
   | Développement | `localhost` sur le poste de chaque étudiant | — | Anonymisées |
   | Recette | `recette.bessieres-alumni.org`, déployée par Timothée | Protégée par mot de passe | Anonymisées |
   | Production | `www.bessieres-alumni.org` | — | Réelles, après bascule uniquement |

   Les étudiants n'ont jamais accès aux données réelles.

## 5. Slack : bien, à une condition

Slack convient, et tu n'as pas besoin d'en changer. Sa limite est que la version gratuite **n'affiche que 90 jours d'historique**, alors que le projet dure six mois. La règle est donc simple :

- **Slack pour discuter.**
- **GitHub pour tout ce qui doit rester** : une tâche est une *issue*, une décision est une *issue* ou un fichier dans `docs/`, un livrable est une *pull request*.
- L'application GitHub pour Slack poste les PR et les *issues* dans un canal `#alumni-dev`. On voit tout passer sans rien recopier.

Un canal par domaine n'est pas utile à quatre. Deux canaux suffisent : `#alumni-dev` (automatique) et `#alumni` (discussion).

## 6. Ce qu'on apprendra en route

Personne ne maîtrise tout au départ. Voici ce que le projet va mobiliser.

| Domaine | Niveau attendu |
|---|---|
| **Git et GitHub** | Branche par tâche, commits clairs, *pull request*, relecture, résolution de conflits, `rebase` sur `main` |
| **Le framework retenu** | Routes, vues, formulaires, modèle et migrations, connexion et droits, back-office |
| **SQL / PostgreSQL** | Modèle relationnel, jointures, index, lecture d'un plan d'exécution simple |
| **Front** | HTML et CSS (Tailwind), un peu de JavaScript, responsive *mobile-first* |
| **Tests** | Tests unitaires et fonctionnels du framework, un scénario par fonction livrée |
| **Docker** | Lancer, arrêter, lire des logs, se connecter à la base |
| **IA** | Rédiger une demande précise, **relire et comprendre** ce qui est généré, ne rien fusionner qu'on ne sait pas expliquer |
| **RGPD** | Savoir quelles données sont personnelles, qui peut les voir, et comment on les efface |

## 7. Gestion de projet : léger mais tenu

Trois rituels suffisent, et ils laissent aussi des traces utiles pour l'épreuve E6 :

- **Un tableau GitHub** à quatre colonnes : À faire, En cours, En relecture, Terminé. Une carte = une issue.
- **Un point de 10 minutes chaque matin**, à l'oral : ce que j'ai fini, ce que je fais, ce qui me bloque.
- **Une démo chaque vendredi**, sur le site de recette.

On s'en tient là : pas de diagramme de Gantt, pas de compte rendu écrit quotidien, pas d'estimation en points.

## 8. Le cycle d'une tâche

```text
Issue (assignée)  →  branche  →  commits  →  Pull Request
     →  relecture par un autre étudiant  →  validation et fusion par Timothée
     →  déploiement automatique en recette
```

La branche `main` est protégée : personne ne pousse directement dessus, et seul Timothée fusionne.

## 9. Où vit la documentation

**Dans le dépôt Git, en Markdown, dans `docs/`.** C'est la seule source de vérité.

- **Pourquoi pas Google Drive ?** La documentation y vit à côté du code au lieu de vivre avec lui : elle se périme sans que personne ne le voie. Et les IA ne la lisent pas.
- **Pourquoi Markdown plutôt qu'AsciiDoc ?** Les fichiers de contexte des IA (`AGENTS.md`, `CLAUDE.md`) sont en Markdown, GitHub l'affiche nativement, et tout le monde l'écrit déjà. Deux formats, ce serait une règle de plus à retenir.
- **Et la page web partagée ?** C'est une **vitrine** pour les personnes qui ne vont pas sur GitHub (chef de travaux, direction), régénérée depuis `docs/` quand c'est utile. On n'édite jamais la page : on édite `docs/`.
