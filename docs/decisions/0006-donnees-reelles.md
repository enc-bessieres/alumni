# 0006 — Les exports réels de Datalumni sur les postes de l'équipe

**Date :** mercredi 25 novembre 2026
**Statut :** décidée par Timothée Robert

## Contexte

Jusqu'ici, la règle 1 d'AGENTS.md interdisait toute donnée réelle sur les postes des étudiants : l'équipe travaillait sur un export factice, dont le format était une hypothèse (`docs/migration/export-factice.md`).

Le 25 novembre, Datalumni a donné à l'ENC les exports de la plateforme : l'annuaire, les offres, les candidatures, les mentorats et l'enquête d'insertion. Ils sont décrits dans `docs/migration/export-reel.md`. Le format réel diffère de l'hypothèse, et le volume aussi : 6138 comptes au lieu d'environ 1300.

Datalumni a aussi confirmé qu'elle ne fournit pas les mots de passe, même hachés.

## Décision

1. **Les étudiants reçoivent les exports réels**, pour écrire l'import sur le vrai format et mesurer les performances sur le vrai volume.
2. **Les mots de passe ne sont pas repris.** Chaque membre définit le sien par un lien reçu par e-mail (voir `docs/migration/export-reel.md`).

## Ce que ça implique pour chacun

Ces fichiers contiennent les noms, adresses e-mail et téléphones de 6138 personnes, et des liens vers des CV. Chaque membre de l'équipe en est responsable sur son poste.

- **Un seul emplacement :** le dossier `sources/` à la racine du projet. Il est ignoré par Git (`.gitignore`) et par Docker (`.dockerignore`). Avant d'y poser les fichiers, on récupère `main` et on vérifie que `git status` ne les montre pas.
- **Jamais dans le dépôt.** Le dépôt est public : un fichier commité est publié, et le reste même après suppression. Pas de `git add -f`, pas de copie dans un autre dossier du projet.
- **Jamais dans une IA.** On ne colle ni fichier, ni ligne, ni capture d'écran d'une donnée réelle dans Claude, Copilot ou un autre assistant. Pour demander de l'aide, on donne les noms des colonnes (`docs/migration/export-reel.md`) ou une ligne de l'export factice.
- **Jamais dans Slack, une issue, une PR ou un commit.** Un bug se décrit avec l'identifiant de la ligne (`user_id`), pas avec le nom de la personne.
- **Pas de copie ailleurs :** ni clé USB personnelle, ni messagerie, ni espace de stockage en ligne, ni ordinateur personnel.
- **Les tests et les démos restent sur les fausses données.** L'intégration continue n'a pas accès aux fichiers réels : un test qui en dépend échoue. Le générateur d'export factice produit le même format, au même volume.
- **Suppression le vendredi 18 décembre :** chacun supprime le dossier `sources/` et sa base locale (`docker compose down -v`) avant de quitter le stage.

## À confirmer

- L'avis du DPO sur cet accès reste à demander (Philippe Chenut).
