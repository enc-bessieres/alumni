# Audit de l'existant — bessieres-alumni.org

*Relevé du 8 novembre 2026, depuis un compte membre (pas administrateur).*

## 1. Architecture technique

| Élément | Constat |
|---|---|
| Éditeur | **Datalumni** (SaaS, abonnement annuel) |
| Front | Nuxt (Vue), multilingue fr/en, installable en PWA (bandeau iOS) |
| API | REST JSON sous `/api/…`, jeton Bearer en `sessionStorage` (`dtlmn-access`). Probablement Django REST Framework : cookie `csrftoken` (nom par défaut de Django), adresses terminées par `/`. À confirmer avec Datalumni |
| Authentification | **Authentik 2025.4** sur `auth.datalumni.com`, en OIDC. E-mail + mot de passe, Google, LinkedIn, inscription libre (`freereg`), récupération de mot de passe |
| Médias | `media3.datalumni.com` (proxy d'images redimensionnées) |
| Statistiques | Matomo (`analytics3.datalumni.com`) |
| Chat de support | Brevo Conversations |
| Pages légales | CGU, confidentialité, charte du mentorat : **hébergées chez Datalumni**, pas chez l'ENC |

**Conséquence pour la migration :** les mots de passe sont stockés dans Authentik, pas dans le site. Authentik les conserve au format Django (`pbkdf2_sha256` par défaut). Notre site peut vérifier ce format puis ré-enregistrer le mot de passe au premier login.

## 2. Données (relevé par l'API)

- **1214 membres** visibles dans l'annuaire :

  | Catégorie | Membres |
  |---|---|
  | Alumni | 1143 |
  | Enseignant | 50 |
  | Équipe administrative | 10 |
  | Étudiant | 9 |
  | Candidat | 9 |
  | Recruteur | 1 |

- **Origine des comptes :**
  - 784 importés en masse (`imports/v2`), dont la grosse vague d'**avril 2025** (590 acceptations des CGU ce mois-là) ;
  - 423 inscrits seuls (`freereg/v2`) ;
  - depuis, 10 à 60 inscriptions par mois.
- **Taux de remplissage des profils :**

  | Élément renseigné | Profils | Part |
  |---|---|---|
  | Photo | 296 | 24 % |
  | Expérience | 340 | 28 % |
  | Localisation | 639 | 53 % |

  La moitié des membres n'apparaît donc **pas sur la carte**.
- **Engagement déclaré :**
  - 179 mentors et 113 mentorés déclarés ;
  - 275 en recherche d'opportunité ;
  - 291 abonnés à la newsletter ;
  - 635 visibles des recruteurs.
- **Structure de l'école** (groupes hiérarchiques) :
  - sites : ENC Bessières, ENC Bessières Apprentissage ;
  - niveaux : BTS, Prépa ;
  - 20 diplômes : ATS, BTS Assurance, CG, CI, Communication, GPME, MCO, NDRC, PIM, SAM, SIO, Tourisme, D1, D2, DCG, DCG2, DCG3, DSCG, ECG, ECT ;
  - un groupe « Validateur » ;
  - un groupe « SPG », dont le sens est à identifier (`/api/user/timeline/spg/`).

  L'année de promotion est portée par une *timeline* propre à chaque appartenance de groupe.

### Modèle d'un profil (`/api/user/{id}/profile/`)

- `metadata` : civilité, prénom, nom, nom de naissance, photo, résumé, CV, localisation géocodée (lat/long, pays, région, département, commune).
- `experiences[]` : intitulé, organisation, début, fin, poste actuel, description, secteur, lieu.
- `educations[]` : intitulé, établissement, année, type de diplôme, restreint ou non.
- `skills[]` (bilingues), `hobbies[]`, `external_links`.
- `groups[]` : catégorie et timelines (diplôme et promo).
- `mentoring` : mentor ou mentoré, types de mentorat, nombre maximum de mentorés.
- `features` :
  - visibilité (annuaire, recruteurs, carte et champs exposés) ;
  - notifications (newsletter, événements, clubs, messages, offres) ;
  - recherche d'opportunité ;
  - tags.
- `last_profile_update`.

## 3. Inventaire fonctionnel

### Côté membre (menu)

| Module | Fonctions | Usage réel |
|---|---|---|
| Accueil | Bandeau, 2 articles à la une, chiffres clés, derniers inscrits, encart mentorat | — |
| À propos | Page éditable + trombinoscope de l'équipe | **« Lorem ipsum » encore en ligne** |
| Annuaire | Recherche par mot-clé, lieu, catégorie ; filtres avancés en fenêtre (campus, promo, mentorat, recherche d'opportunité, secteur, diplôme) ; vue cartes + vue carte géographique ; bouton Message | 1214 fiches, 12 par page |
| Groupes (clubs) | Création soumise à validation, adhésion, posts, invitations, hiérarchie des groupes | **1 club visible** (Amicale des personnels, 4 membres, en attente de validation) |
| Mentorat | Liste des mentors, filtres par sujet, « Solliciter comme mentor », appariement, retour d'expérience, charte | 179 mentors, aucune relation visible |
| Actualités | Fil mêlant articles, posts, événements, offres, mentorat | **31 éléments au total, dernier le 19/03/2026** |
| Blog | Articles avec vues, likes, commentaires, signalement, validation | **14 articles**, 12 à 118 vues, **0 commentaire** |
| Événements | Création, inscription, médias, visibilité restreinte, partage, calendrier | **2 événements** (nov. 2025, janv. 2026) |
| Emplois/stages | Dépôt, validation, candidature, suivi des candidatures, export, contrat, salaire, expérience | **0 offre publiée** |
| Ressources | Fichiers filtrables par type et catégorie | **Vide** |
| Messagerie | Conversations privées, non lus | — |
| Paramètres | Compte, visibilité, notifications, blocage, motivations, préférences de mentorat | — |
| Inscription | Parcours en étapes : e-mails, mot de passe, données personnelles, catégories, questionnaire, CGU, validation par un « Validateur » (en attente ou refusée) | — |

### Côté administration (repéré dans le code du front, non visité)

- **Utilisateurs :**
  - imports, changement de rôle en masse, rôles, catégories, sites, diplômes, hiérarchie, tags ;
  - relance des inactifs (`inactive-users/send-invitations`) ;
  - validations.
- **Communication :** newsletters, envoi groupé (`masschat`), campagnes.
- **Insertion :** enquête d'insertion, **France Compétences**.
- **Plateforme :** activation des modules, page d'accueil, pages libres, charte graphique, listes de valeurs, barres de recherche, questionnaire d'inscription.
- **Interopérabilité : API à clés** (`settings/platform/interoperability/api`) et **exports** : c'est la voie normale pour récupérer les données.
- Tableau de bord et statistiques.

> **À vérifier par Philippe Chenut (DDFPT)** avec un accès administrateur :
> - l'enquête d'insertion France Compétences est-elle utilisée ? C'est une obligation pour les certifications en apprentissage, et c'est peut-être la vraie valeur de l'abonnement ;
> - les newsletters sont-elles envoyées depuis Datalumni ?
> - l'API d'export est-elle incluse dans l'abonnement ?

## 4. Ce qui freine l'usage

Ces remarques portent sur l'**outil** Datalumni. La plupart viennent de choix de l'éditeur, que l'ENC ne peut pas modifier.

1. **Annuaire sans tri ni regroupement.**
   - On ne choisit pas l'ordre d'affichage, et on ne peut pas regrouper par promo ou par diplôme.
   - La filière est dans la fenêtre « Tous les filtres ». Le filtre visible « Catégorie » propose Alumni, Étudiant, Enseignant…
   - Les cartes sont grandes : 12 par page, et un carré gris remplace les photos manquantes.
   - Le diplôme et la promo ne figurent pas sur la carte d'un membre.
2. **Carte géographique sans légende.** Elle ne montre que les membres qui ont indiqué leur ville, soit environ la moitié, sans dire de quelle filière ils sont.
3. **Menu latéral en icônes seules.** Le libellé n'apparaît qu'au survol, ce qui est impossible sur un téléphone.
4. **Modules affichés même vides** (Emplois, Ressources), ce qui donne une impression d'inactivité. Un texte provisoire « Lorem ipsum » est resté sur la page À propos.
5. **Rien n'incite à revenir** : pas de résumé hebdomadaire, pas de notification sur le téléphone.
6. **Peu d'étudiants actuels** (9 comptes), alors que ce sont eux qui ont un besoin immédiat (stage, alternance, premier emploi).
7. **Profils longs à remplir**, sans possibilité de reprendre son CV ou son LinkedIn.

## 5. Diagnostic

Les fonctions sont là, mais l'usage manque. Une plateforme de ce type demande une animation régulière, et l'outil actuel ne donne pas beaucoup de raisons de revenir.

Reproduire les fonctions ne suffira donc pas. La nouvelle plateforme doit **faire venir les étudiants** et donner aux alumni **des raisons de revenir**. C'est l'objet de [03-evolutions.md](03-evolutions.md).
