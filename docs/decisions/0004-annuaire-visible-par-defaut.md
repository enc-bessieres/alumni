# 0004 — Annuaire : membres visibles par défaut

**Date :** lundi 23 novembre 2026
**Statut :** décidée (proposée par M. Robert à la démo et validée à l'oral) ; pages légales à faire relire par le DPO

## Contexte

Avec l'annuaire (#41), un membre n'y apparaissait que s'il cochait « Apparaître dans l'annuaire » dans Paramètres (#51) : c'était l'application stricte de la règle 5 d'AGENTS.md (« toute donnée personnelle est privée par défaut »).

À la démo du lundi 23 novembre, M. Robert a proposé l'inverse, et l'équipe l'a retenu : un annuaire vide tant que chacun n'est pas allé cocher une case ne remplit pas son rôle, qui est de retrouver ses anciens camarades. C'est aussi ce que fait Datalumni aujourd'hui : l'annuaire montre 1214 membres, et seuls quelques-uns s'en sont retirés (docs/01-audit-existant.md).

## Décision

`visible_dans_annuaire` vaut **vrai** par défaut. Le membre peut se retirer à tout moment dans Paramètres, et la case lui dit ce qui est montré.

Ce qui est montré par défaut est limité à ce qu'un annuaire d'anciens élèves rend attendu, et seulement aux **membres validés** :

| Information | Par défaut |
|---|---|
| Nom, prénom, catégorie | visible dans l'annuaire |
| Diplômes, sites et promos | visible dans l'annuaire |
| Adresse e-mail | **cachée** (le membre peut la montrer sur sa fiche) |
| Profil LinkedIn | montré seulement si le membre le renseigne lui-même |

## Ce que ça implique

- La règle 5 d'AGENTS.md gagne une exception écrite : la présence dans l'annuaire (nom, catégorie, diplômes). Tout le reste du profil reste privé par défaut.
- Les comptes déjà en base gardent leur choix ; l'import Datalumni (#37) reprend `visible_annuaire` de chaque membre.
- RGPD : les CGU et la politique de confidentialité doivent dire, avant l'inscription, que le membre apparaît dans l'annuaire des membres validés et comment s'en retirer. À faire relire par le DPO (Philippe Chenut porte l'échange).
