# 0005 — Entrer sur le site sans attendre la validation

**Date :** mardi 24 novembre 2026, précisée le jeudi 26 novembre
**Statut :** décidée par M. Robert (démo du 23 novembre), précisée par écrit le 26 novembre ; pages légales à faire relire par le DPO (#81)

## Contexte

La répartition prévoyait une inscription « validée par un rôle Validateur », comme chez Datalumni : on ne pouvait rien faire avant la validation. Pour un site encore peu connu, attendre plusieurs jours fait perdre les nouveaux inscrits : quand leur compte est enfin ouvert, ils n'y pensent plus.

## Décision

1. **Un nouvel inscrit entre sur le site dès que son adresse e-mail est vérifiée** : le lien de vérification le connecte.
2. **L'annuaire et les fiches restent réservés aux membres dont l'inscription a été validée par un validateur.** Jusque-là, son inscription est « en attente » ; il voit une page qui l'explique.

La règle est la même pour toutes les catégories, recruteurs compris.

Précision de M. Robert, le 26 novembre : « l'annuaire et les fiches restent réservés aux membres dont l'inscription a été validée par un validateur. Un nouvel inscrit entre sur le site dès que son adresse est vérifiée, mais il ne voit l'annuaire qu'après validation. »

## Précautions

| Risque | Précaution |
|---|---|
| Faux comptes, adresses inventées | Vérification de l'adresse e-mail obligatoire (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`) |
| Robots qui créent des comptes en masse | Champ piège invisible (`site_web`) et limite d'allauth : 5 inscriptions par minute et 20 par heure depuis une même adresse IP |
| Inconnu qui parcourt l'annuaire | Inscription « en attente » jusqu'à la validation : `reserve_aux_membres_valides` ferme l'annuaire et les fiches |
| Visiteur qui s'attribue un statut ou des droits | Le statut est fixé par le code (`InscriptionForm.signup`), jamais par ce qui est envoyé ; testé |
| Compte malveillant repéré après validation | Un validateur le passe à « Refusée » : le statut est vérifié à chaque page, il perd l'accès tout de suite, et il ne peut plus se connecter |
| Information des membres (RGPD) | CGU et politique de confidentialité (#81), relues par le DPO |

## Ce que ça implique

- Les validateurs ont une page dédiée, `/validation/` : les inscriptions en attente, de la plus ancienne à la plus récente, avec « Valider » et « Refuser ». Le membre reçoit un e-mail dans les deux cas. Le back-office permet aussi de changer le statut, mais sans e-mail : la page est le chemin normal.
- Import Datalumni : l'export ne contient pas de statut d'inscription ; un compte activé chez Datalumni est considéré comme validé (`docs/migration/export-reel.md`). Les comptes jamais activés suivent la première connexion (#85).
