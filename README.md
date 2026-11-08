# Alumni ENC Bessières

Plateforme du réseau des anciens de l'ENC Bessières. Elle remplacera la plateforme Datalumni sur https://www.bessieres-alumni.org/ avant le 25 mars 2027.

Le projet est réalisé par des étudiants de BTS SIO SLAM, de novembre à décembre 2026, sous la responsabilité de Timothée Robert.

## Démarrer

> Cette section est complétée le lundi 9 novembre au soir, une fois la technique choisie.

Seuls **Git** et **Docker Desktop** sont nécessaires.

```bash
git clone https://github.com/enc-bessieres/alumni.git
cd alumni
cp .env.example .env
docker compose up
```

## Documentation

- [Audit de l'existant](docs/01-audit-existant.md)
- [Répartition et calendrier](docs/02-repartition.md)
- [Évolutions](docs/03-evolutions.md)
- [Prérequis et méthode](docs/04-prerequis.md)
- [Choix technique](docs/05-choix-technique.md)
- [Points durs de l'intégration](docs/06-points-durs.md)
- [Comment contribuer](CONTRIBUTING.md)

## Règles

Aucune donnée réelle et aucun secret dans ce dépôt. Le reste des règles est dans [AGENTS.md](AGENTS.md).
