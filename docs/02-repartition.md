# Répartition du travail — parité avec Datalumni

**Objectif de la bascule (mars-avril 2027) :** au moins tout ce que fait Datalumni aujourd'hui, avec les données migrées.

Les modules vides (Emplois, Ressources, Clubs) sont reproduits **simplement**. Ils seront enrichis ensuite, voir [03-evolutions.md](03-evolutions.md).

Chaque étudiant est **responsable d'un domaine**, de la base de données à l'écran. Timothée intègre et déploie. Philippe Chenut (DDFPT) porte les échanges avec Datalumni et les contacts institutionnels.

## Axel Xu — Comptes, profils, annuaire

C'est le socle : tout le monde en dépend, il passe donc en premier.

- **Connexion :**
  - e-mail + mot de passe ;
  - première connexion après la bascule : le membre saisit son e-mail, puis modifie son mot de passe (déjà inscrit chez Datalumni) ou le définit (jamais inscrit), par un lien reçu par e-mail (voir `docs/migration/export-reel.md`) ;
  - Google, LinkedIn ;
  - mot de passe oublié ;
  - déconnexion.
- **Inscription en étapes :**
  - e-mail, mot de passe, données personnelles ;
  - choix de la catégorie (Alumni, Étudiant, Enseignant, Candidat, Équipe administrative, Recruteur) ;
  - diplôme et promo, CGU ;
  - validation par un rôle « Validateur » (en attente, acceptée, refusée).
- **Rôles et droits :**
  - membre, validateur, administrateur ;
  - qui voit quoi, géré à **un seul endroit**.
- **Profil :**
  - identité : civilité, nom de naissance, photo avec recadrage, résumé, CV en PDF ;
  - localisation géocodée ;
  - expériences, formations, compétences, centres d'intérêt, liens externes.
- **Paramètres du compte :**
  - visibilité (annuaire, recruteurs, carte et champs exposés) ;
  - notifications ;
  - blocage d'un membre ;
  - suppression du compte (RGPD).
- **Annuaire :**
  - recherche ;
  - filtres : lieu, catégorie, campus, diplôme, promo, mentor, recherche d'opportunité, secteur ;
  - vue liste + vue carte.

## Luc Zhang — Migration des données, administration, recette

C'est le chemin critique : il commence dès l'obtention d'un premier export.

- **Scripts d'import** Datalumni → nouvelle base :
  - membres, profils, groupes et timelines (diplôme, promo) ;
  - articles, posts, événements, médias (rapatriés depuis `media3.datalumni.com`).
- **Comptes :**
  - import sans mot de passe, depuis le CSV réel de l'annuaire (6138 comptes, dont 1233 activés) ;
  - rapprochement Google/LinkedIn par e-mail vérifié ;
  - rapport des comptes en doublon ou sans e-mail.
- **Répétitions :** script rejouable de bout en bout et **3 migrations à blanc** chronométrées avant la bascule.
- **Administration :**
  - référentiels : sites, niveaux, diplômes, tags, secteurs, types de contrat ;
  - import CSV de membres, pour les promos sortantes et les étudiants actuels ;
  - changement de rôle en masse ;
  - export.
- **E-mails :** envoi transactionnel (inscription, mot de passe, notifications) et envoi groupé ou newsletter, avec désinscription.
- **Recette :** jeu de données anonymisé pour le développement, scénarios de test par module, liste des écarts avec Datalumni.

## Steeve Zhou — Mise en relation

- **Mentorat :**
  - se déclarer mentor ou mentoré, avec les sujets et le nombre maximum de mentorés ;
  - liste des mentors filtrable ;
  - « Solliciter comme mentor », puis acceptation ou refus ;
  - retour d'expérience en fin de relation ;
  - charte.
- **Chat en direct, repris du prototype de 2026** (branche `main` d'Alumni_Clone) et réécrit en Django, avec la même technique (SSE). C'est une fonction que Datalumni n'a pas :
  - présence des membres connectés ;
  - salon public ;
  - messages privés en temps réel, avec fichiers ;
  - forum mis à jour en direct ;
  - modération (filtre, signalement, blocage) ;
  - messagerie flottante sur toutes les pages ;
  - notification par e-mail des messages reçus hors connexion.
- **Groupes / clubs :**
  - création soumise à validation, adhésion libre ou sur demande ;
  - membres ;
  - posts du groupe, invitations.
- **Notifications** dans le site : cloche, liste, marquer comme lu.

## Marie Dominique Dzalamou — Contenus et vie du réseau

- **Page d'accueil :**
  - bandeau, articles à la une, chiffres clés ;
  - derniers inscrits, encart mentorat.
- **Pages libres** éditables (À propos, mentions légales, CGU, confidentialité **propres à l'ENC**).
- **Blog / actualités :**
  - articles avec image, rédaction, validation, publication ;
  - vues, likes, commentaires, signalement.
- **Fil d'actualité :** posts des membres et agrégation des articles, événements et offres.

Les événements, les offres et les ressources, d'abord prévus dans ce domaine, sont confiés à Sidouane et Vera depuis le 25 novembre.

## Sidouane Chendjou — Événements

Dans l'équipe du 25 novembre au 18 décembre. Issues #60 à #66.

- **Événements :**
  - création dans le back-office, puis proposition par un membre, soumise à publication ;
  - liste des événements à venir et passés, page d'un événement ;
  - inscription et désinscription, places limitées ;
  - liste des participants, visible selon le choix de chaque inscrit ;
  - export vers un agenda (fichier `.ics`).
- **Plus tard :** visibilité restreinte à un groupe (dépend des groupes de Steeve), image de l'événement (dépend du stockage des fichiers).

## Vera Miremma — Emplois et stages

Dans l'équipe du 25 novembre au 18 décembre. Issues #67 à #73.

- **Offres d'emploi et de stage :**
  - dépôt par un membre, validation dans le back-office ;
  - contrat (référentiel de Luc, #39), lieu, rémunération, expérience ;
  - liste filtrable par mot-clé, type de contrat et lieu ;
  - candidature, envoyée par e-mail au contact de l'offre.
- **Plus tard :** candidature avec le CV du profil (dépend du profil d'Axel).

## Sidouane et Vera — Ressources

En binôme, la dernière semaine. Issue #74.

- **Ressources :** documents classés par catégorie, d'abord sous forme de liens.

## Relectures croisées

| L'auteur | est relu par |
|---|---|
| Steeve | Axel |
| Marie Dominique | Luc |
| Axel | Luc |
| Luc | Axel |
| Sidouane | Vera |
| Vera | Sidouane |

Chaque demande de fusion est relue par un étudiant **avant** que Timothée la valide.

## Calendrier : stage du lundi 9 novembre au vendredi 18 décembre 2026

Le stage commence **demain** : il n'y a pas de socle prêt. La première semaine sert donc à le construire **ensemble**, chacun sur une brique dont il aura besoin ensuite. Le mercredi 11 novembre est férié.

### Semaine 1 — démarrage et socle (9 au 13 novembre)

| Jour | Matin | Après-midi |
|---|---|---|
| **Lundi 9** | Présentation du projet (la page de cadrage) ; vérification des postes ; chacun découvre son domaine dans la plateforme actuelle et dans le prototype 2026 | Mini-tâche de 2 h dans l'option technique qui tente chacun, puis **décision à 17 h** (voir [05-choix-technique.md](05-choix-technique.md)) |
| **Mardi 10, jeudi 12, vendredi 13** | Socle, une brique chacun | Le vendredi après-midi, **socle fusionné** et première démo |

Les briques du socle sont réparties ainsi :

- **Axel :** modèle Membre, connexion par e-mail et mot de passe, rôles.
- **Luc :** référentiels (sites, niveaux, diplômes, promos) et **générateur de fausses données** reproduisant la structure Datalumni, en attendant l'échantillon réel.
- **Steeve :** gabarit des pages (menu avec libellés, mise en page mobile d'abord, Tailwind), manifeste PWA.
- **Marie Dominique :** back-office d'administration et pages libres (À propos, mentions légales, CGU).

**État au mardi 17 novembre :** le socle est entièrement fusionné dans `main`, deux jours ouvrés après la date prévue. Les quatre briques sont livrées (16 pull requests fusionnées depuis le 10 novembre), il ne reste aucune pull request ouverte et les 125 tests passent. La parité par domaine commence le mercredi 18 novembre.

### Semaines 2 à 6

| Semaine | Dates | Objectif |
|---|---|---|
| S2 | 16 – 20 nov. | Fin du socle lundi et mardi, puis début de la parité par domaine. À livrer avant la démo du vendredi 20 : la connexion des faux membres (Luc) et l'éditeur de texte des pages (Marie Dominique) |
| S3 – S4 | 23 nov. – 4 déc. | Parité par domaine |
| S5 | 7 – 11 déc. | Fin de la parité, puis évolutions rapides : tri et regroupement de l'annuaire, PWA, partage |
| S6 | 14 – 18 déc. | Recette croisée (chacun teste le domaine d'un autre), corrections, documentation, **démo finale** devant le chef de travaux |

Le rythme de chaque semaine, depuis la semaine 2 :

- **Mardi à 16 h 30 et vendredi à 11 h 30 :** séance de fusion. Une pull request relue et approuvée avant la séance est fusionnée pendant la séance.
- **Vendredi à 15 h :** démo.

### Pendant ce temps

| Quand | Philippe : Datalumni et contacts institutionnels | Timothée : technique |
|---|---|---|
| Lundi 9 | **Récupérer un accès administrateur Datalumni**, pour voir tout le contenu, les exports et l'enquête d'insertion ; envoyer la demande d'export ([06-points-durs.md](06-points-durs.md) § 8) | Créer l'organisation GitHub, le dépôt et les tâches |
| Semaine 1 | Savoir qui possède le domaine et qui administre la page LinkedIn de l'école | Protéger `main`, fusionner le socle, mettre en ligne la recette |
| Avant S2 | — | Créer les applications Google et LinkedIn **de développement** |
| En continu | Relances Datalumni, DPO, direction | Données anonymisées dès l'échantillon reçu ; relecture et fusion ; démo du vendredi |

### Après le stage

| Quand | Quoi |
|---|---|
| Janvier – février | Intégration et compléments par Timothée ; compléments possibles en atelier et dans le cadre de l'épreuve E6 ; hébergement de production ; 2 à 3 migrations à blanc |
| Avant le **25 mars 2027** | Bascule sur bessieres-alumni.org (le domaine expire ce jour-là) |
| Avril – juin | Évolutions réseaux sociaux et mobile |
