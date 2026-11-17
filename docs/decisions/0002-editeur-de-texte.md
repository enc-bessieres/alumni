# 0002 — Éditeur de texte pour les contenus

**Date :** lundi 16 novembre 2026
**Statut :** décidée

## Contexte

Les pages libres, et plus tard le blog, les événements et les offres, ont besoin de mise en forme : titres, gras, listes, liens. Aujourd'hui, le contenu est saisi et affiché en texte brut : le HTML est échappé pour se protéger contre le XSS, donc aucune mise en forme n'est possible.

## Décision

Utiliser l'éditeur de texte **django-prose-editor**, avec le nettoyage du HTML par **nh3**.

| Élément | Version |
|---|---|
| django-prose-editor (option `[sanitize]`) | ~=0.28.0 |
| nh3 | installé par l'option `[sanitize]` |

## Raisons

1. Le site s'adresse à un public large : alumni, étudiants, enseignants, recruteurs. Le Markdown ou les balises HTML demandent d'apprendre des symboles, ce qui serait un frein. Un éditeur avec des boutons ne demande rien à apprendre, comme dans le prototype de 2026.
2. Avec django-prose-editor, la liste des mises en forme autorisées est déclarée une seule fois : elle sert à la fois aux boutons de l'éditeur et au nettoyage du HTML par nh3. Avec les autres éditeurs, il faut tenir deux listes à la main, et c'est là que naissent les failles XSS.
3. Il est fait pour Django, maintenu activement, sous licence BSD, et son JavaScript est livré dans le paquet, sans npm ni CDN.
4. Les autres éditeurs ont été écartés : CKEditor 5 et TinyMCE (licence GPL ou payante, plus lourds), Quill et Summernote (abandonnés), Trix (un seul niveau de titre), Editor.js (stocke du JSON au lieu du HTML).

## Ce que ça implique

- Une application `texte_riche` déclare une seule fois le champ `ChampTexteRiche` et les mises en forme autorisées. Le blog, les événements et les offres l'utiliseront aussi.
- Le nettoyage se fait quand un formulaire est validé, pas à l'enregistrement. Les migrations de données et l'import Datalumni doivent donc appeler `nettoyer()`.
- L'affichage utilise `|safe`, ce qui n'est acceptable que parce que le contenu a été nettoyé avant.
- Limites : un seul mainteneur, et une version 0.x dont l'interface peut changer. C'est acceptable, car le contenu est stocké en HTML standard dans un champ texte ordinaire : si la bibliothèque disparaît, les données restent lisibles et on peut changer d'éditeur sans rien convertir. La version est figée avec `~=0.28.0`.