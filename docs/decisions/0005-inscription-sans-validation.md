# 0005 — Inscription sans validation préalable (sauf recruteurs)

**Date :** mardi 24 novembre 2026
**Statut :** décidée (proposée par M. Robert à la démo du 23 novembre) ; pages légales à faire relire par le DPO

## Contexte

La répartition prévoyait une inscription « validée par un rôle Validateur », comme chez Datalumni. Pour un site encore peu connu, attendre plusieurs jours la validation fait perdre les nouveaux inscrits : quand leur compte est enfin ouvert, ils n'y pensent plus.

## Décision

Un nouveau membre entre dès que son **adresse e-mail est vérifiée**, et il est connecté en cliquant le lien de vérification. Seule exception : un **recruteur** attend la validation de l'équipe, car il n'est pas un ancien de l'école et c'est le profil le plus tenté de collecter les données de l'annuaire.

## Précautions (obligatoires)

| Risque | Précaution |
|---|---|
| Faux comptes, adresses inventées | Vérification de l'adresse e-mail obligatoire (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`) |
| Robots qui créent des comptes en masse | Champ piège invisible (`site_web`) et limite d'allauth : 5 inscriptions par minute et 20 par heure depuis une même adresse IP |
| Recruteur qui parcourt l'annuaire | Catégorie Recruteur : statut « en attente » jusqu'à la validation |
| Compte malveillant repéré après coup | Un validateur le passe à « Refusée » : `reserve_aux_membres_valides` vérifie le statut à chaque page, il perd l'accès tout de suite. Le back-office filtre les comptes par date d'inscription pour les passer en revue |
| Visiteur qui s'attribue un statut ou des droits | Le statut est fixé par le code (`InscriptionForm.signup`), jamais par ce qui est envoyé ; testé |
| Information des membres (RGPD) | CGU et politique de confidentialité : l'annuaire est visible des membres inscrits sans validation préalable (avec la décision 0004) ; relecture par le DPO |

## Ce que ça implique

- La PR 3 de l'inscription devient un **contrôle après coup** : revue des nouveaux comptes, refus, et validation des recruteurs, avec un e-mail au membre.
- Import Datalumni : l'export ne contient pas de statut d'inscription ; un compte activé chez Datalumni est considéré comme validé (`docs/migration/export-reel.md`). Les comptes jamais activés suivent la première connexion (#85).
