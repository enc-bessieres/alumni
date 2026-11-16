# Alumni ENC Bessières

Plateforme du réseau des anciens de l'ENC Bessières. Elle remplacera la plateforme Datalumni sur https://www.bessieres-alumni.org/ avant le 25 mars 2027.

Le projet est réalisé par des étudiants de BTS SIO SLAM, de novembre à décembre 2026, sous la responsabilité de Timothée Robert.

## Démarrer

Seuls **Git** et **Docker Desktop** sont nécessaires. Les commandes se tapent dans **Git Bash**.

```bash
git clone https://github.com/enc-bessieres/alumni.git
cd alumni
cp .env.example .env
docker compose up
```

Le premier lancement télécharge les images et prend quelques minutes. Ensuite :

| Adresse | Quoi |
|---|---|
| http://localhost:8000 | Le site |
| http://localhost:8000/admin/ | Le back-office (créer d'abord un compte, voir ci-dessous) |
| http://localhost:8026 | Mailpit : les e-mails envoyés par le site |
| `localhost:5433` | PostgreSQL, pour DBeaver (base, utilisateur et mot de passe dans `.env`) |

Le code est partagé avec le conteneur : une modification s'affiche sans relancer Docker.

## Commandes utiles

Dans un second terminal, pendant que `docker compose up` tourne :

| Pour… | Commande |
|---|---|
| Lancer les tests | `docker compose exec web python manage.py test` |
| Créer un compte administrateur | `docker compose exec web python manage.py createsuperuser` |
| Créer les migrations après avoir modifié un modèle | `docker compose exec web python manage.py makemigrations` |
| Appliquer les migrations | `docker compose exec web python manage.py migrate` |
| Charger les fausses données | `docker compose exec web python manage.py charger_donnees_dev` |
| Vérifier le style | `docker compose exec web ruff check .` puis `docker compose exec web ruff format .` |
| Repartir d'une base vide | `docker compose down -v` puis `docker compose up` |

L'intégration continue (GitHub Actions) lance le style, les migrations et les tests à chaque pull request.

## Documentation

- [Audit de l'existant](docs/01-audit-existant.md)
- [Répartition et calendrier](docs/02-repartition.md)
- [Évolutions](docs/03-evolutions.md)
- [Prérequis et méthode](docs/04-prerequis.md)
- [Choix technique](docs/05-choix-technique.md)
- [Points durs de l'intégration](docs/06-points-durs.md)
- [Référentiels et fausses données de développement](docs/donnees-de-developpement.md)
- [Comment contribuer](CONTRIBUTING.md)

## Règles

Aucune donnée réelle et aucun secret dans ce dépôt. Le reste des règles est dans [AGENTS.md](AGENTS.md).
