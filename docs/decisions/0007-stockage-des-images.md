# 0007 — Stockage des images envoyées par les membres

**Date :** jeudi 26 novembre 2026
**Statut :** proposée (issue #92)

## Contexte

La fiche 0003 a ajouté Pillow et laissé à décider, avec la première fonction qui reçoit une image, où ranger les fichiers envoyés, leur taille maximale et le nettoyage des métadonnées. Le blog (image d'un article), les profils (photo), les événements et la reprise des 14 articles de l'ancien site en ont besoin.

## Décision

| Élément | Choix |
|---|---|
| Dossier | `MEDIA_ROOT = BASE_DIR / "media"`, adresse `MEDIA_URL = "media/"` |
| Dépôt et image Docker | `media/` est ignoré par `.gitignore` et `.dockerignore` |
| Développement | Django sert les fichiers lui-même, seulement quand `DEBUG` est activé |
| Taille maximale | 5 Mo par image |
| Largeur maximale | 1600 px, la hauteur est réduite dans la même proportion |
| Métadonnées | supprimées : l'image est réenregistrée avec Pillow |

Les règles sont dans `images/outils.py`, commun à tout le site :

- `verifier_taille` : validateur à mettre sur un `ImageField` ;
- `nettoyer_image` : à appeler avant d'enregistrer l'image.

## Raisons

1. **RGPD :** les métadonnées EXIF peuvent contenir la position GPS de la prise de vue. Les supprimer évite de publier l'adresse d'un membre sans qu'il le sache.
2. **Performances :** une photo de téléphone fait souvent 4000 px de large et plusieurs Mo. Réduite à 1600 px, elle reste nette à l'écran et charge plus vite, surtout sur mobile.
3. **Une seule règle pour tout le site :** comme `ChampTexteRiche` pour le texte, chaque domaine utilise les mêmes fonctions au lieu d'écrire les siennes.
4. **Aucune image de membre dans le dépôt**, qui est public.

## Ce qui reste à décider

- En production : quel programme envoie les fichiers aux visiteurs, et où ils sont gardés et sauvegardés (en dehors du conteneur, comme la base). À COMPLÉTER avec M. Robert, sur l'issue #92.
