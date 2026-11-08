# Comment contribuer

## Le cycle d'une tâche

```text
Issue assignée  →  branche  →  commits  →  pull request
   →  relecture par un autre étudiant  →  fusion par Timothée  →  recette
```

1. **Prendre une issue.** Assigne-toi une issue de ton domaine, puis passe-la en « En cours » sur le tableau du projet.
2. **Créer une branche à partir de `main` à jour :**

   ```bash
   git switch main
   git pull
   git switch -c luc/6-referentiels
   ```

3. **Travailler par petits commits**, au présent, en français : « Ajoute le modèle Diplôme ».
4. **Avant d'ouvrir la PR, se remettre à jour sur `main` :**

   ```bash
   git fetch
   git rebase origin/main
   ```

   Vérifie ensuite que les tests passent et que l'application démarre.
5. **Ouvrir la pull request.**
   - Elle contient `Ferme #6`, pour fermer l'issue automatiquement à la fusion.
   - Elle dit comment vérifier la fonction.
   - Elle demande la relecture de ton binôme.
6. **Relire et corriger.** Les remarques de la relecture se corrigent dans de nouveaux commits, sur la même branche.
7. **Fusionner.** Timothée fusionne, et personne d'autre.

## Binômes de relecture

| Auteur | Relecteur |
|---|---|
| Steeve | Axel |
| Marie Dominique | Luc |
| Axel | Luc |
| Luc | Axel |

## Ce que vérifie le relecteur

- La PR fait **une seule chose**, celle de l'issue.
- Le code est compréhensible sans explication orale.
- Les droits d'accès passent par le mécanisme du framework, sans contournement.
- Il n'y a ni secret, ni donnée réelle, ni SQL construit à la main.
- Un test vérifie la fonction.
- **Il a lancé l'application et essayé la fonction lui-même.**

## Utiliser une IA

Tu peux utiliser l'IA que tu veux. Le contexte du projet est dans [AGENTS.md](AGENTS.md), qu'elle doit lire. Tu restes l'auteur : ne propose rien que tu ne saurais pas expliquer en relecture.
