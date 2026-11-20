# 0003 — Images envoyées par les membres : Pillow

**Date :** vendredi 20 novembre 2026
**Statut :** décidée

## Contexte

Plusieurs domaines vont recevoir des images : l'image d'un article du blog (Marie Dominique, #43), la photo de profil avec recadrage (Axel), puis les événements et les médias rapatriés de Datalumni (Luc).

Le champ `ImageField` de Django **exige** la bibliothèque Pillow : Django s'en sert pour vérifier qu'un fichier envoyé est vraiment une image et pour lire ses dimensions. Sans elle, il ne reste que `FileField`, qui accepte n'importe quel fichier sans le contrôler. Pour un formulaire ouvert aux membres, ce n'est pas acceptable.

La question est posée par le blog, mais elle concerne tout le projet : la dépendance est donc ajoutée une seule fois, ici, plutôt que par chaque domaine de son côté.

## Décision

Ajouter **Pillow** aux dépendances de l'application.

| Élément | Version |
|---|---|
| Pillow | ~=13.0.0 |

## Raisons

1. C'est la bibliothèque d'images de référence en Python, et celle qu'attend Django : aucune autre ne fait fonctionner `ImageField`.
2. Elle est maintenue activement, sous licence libre (MIT-CMU), et livrée précompilée pour Linux : l'image Docker l'installe avec `pip`, sans bibliothèque système à ajouter.
3. Elle permet de redimensionner et de recadrer les images (photo de profil, vignettes), donc d'éviter de servir des photos de plusieurs mégaoctets sur mobile.
4. Réenregistrer l'image avec Pillow supprime ses métadonnées EXIF, qui contiennent parfois la position GPS de la prise de vue : c'est utile pour le RGPD (règle 5, données privées par défaut).

## Ce que ça implique

- Les images envoyées par les membres utilisent `models.ImageField` (ou `forms.ImageField`), jamais `FileField` : un fichier qui n'est pas une image est refusé par la validation du formulaire.
- Pillow analyse des fichiers envoyés par des inconnus, et des failles y sont corrigées régulièrement. `~=13.0.0` accepte ces correctifs (13.0.x) : il faut reconstruire l'image Docker de temps en temps (`docker compose build --pull`) et surveiller les annonces de sécurité de Pillow, même pendant le gel des versions.
- Le stockage des fichiers envoyés (`MEDIA_ROOT`, `MEDIA_URL`), leur taille maximale et le nettoyage des EXIF restent à décider avec la première fonction qui reçoit une image (le blog) : ce n'est pas l'objet de cette fiche.
