# Évolutions — au-delà de la parité

L'audit montre que les fonctions sont là, mais que l'usage manque. Chaque évolution ci-dessous répond à l'une de trois questions :

1. Est-ce que **trouver quelqu'un** devient facile ?
2. Est-ce que **les étudiants viennent** ?
3. Est-ce que **les alumni reviennent** ?

## 1. Annuaire utilisable — avant la bascule

C'est le cœur du site, et c'est le premier écran que tout le monde jugera.

- **Tri explicite et modifiable :** nom, promo, inscrits récemment, actifs récemment.
- **Regroupement au choix :** par diplôme, promo, campus, ville ou entreprise, en sections repliables avec leur effectif (« BTS SIO — 2019 (14) »).
- **Filtres visibles sous forme de puces**, au lieu d'une fenêtre cachée : diplôme, promo, campus, mentor, « recherche alternance / stage / emploi », secteur.
- **Mots-clés choisis par les membres :**
  - « je peux aider pour : alternance, entretien, création d'entreprise, expertise comptable… » ;
  - une liste fermée gérée par l'administration, pour que le filtrage fonctionne.
- **Carte d'un membre plus utile :**
  - diplôme et promo affichés en premier ;
  - vue compacte en liste ou tableau en plus des cartes ;
  - initiales en couleur au lieu du carré gris.
- **Carte géographique compréhensible :**
  - légende et compteur (« 639 membres ont indiqué leur ville ») ;
  - mêmes filtres que la liste ;
  - un clic sur une grappe affiche les personnes concernées.
- **Recherche partageable** par URL (« tous les DCG en recherche d'alternance »).

## 2. Faire venir les étudiants

Aujourd'hui, 9 étudiants sont inscrits pour 1143 alumni.

- **Import des étudiants à chaque rentrée** par fichier CSV, avec une invitation qui active le compte en un clic.
- **Alternance et stages en tête de site :**
  - offres déposées par les relations entreprises et par les alumni recruteurs ;
  - candidature en un clic avec le CV déjà présent dans le profil.
- **Statut « je cherche »** mis en avant auprès des alumni de la même filière.

## 3. Faire revenir les alumni

- **Résumé hebdomadaire personnalisé**, par e-mail et notification : nouveaux inscrits de ta filière, offres, événements, demandes de mentorat. Rien ne part si rien n'est nouveau.
- **Anniversaires de promo :** « il y a 10 ans, la promo BTS CI 2016… », avec la liste des inscrits.
- **Profil pré-rempli par IA :**
  - le membre dépose son CV ou l'export PDF de son profil LinkedIn ;
  - Claude en extrait expériences, formations et compétences ;
  - le membre valide.

  Cela s'attaque aux 72 % de profils sans expérience. L'API LinkedIn ne donne pas le parcours, d'où ce passage par le PDF.
- **Recherche en langage naturel :** « un expert-comptable DCG près de Lyon qui accepte du mentorat » est traduit en filtres.

## 4. Le chat en direct

Le prototype de 2026 a déjà un chat en direct : membres connectés, salon public, messages privés, forum mis à jour sans recharger. Datalumni n'a rien de comparable.

**Comment ça marche.** Le navigateur garde une connexion ouverte avec le serveur, qui lui pousse les nouveaux messages dès qu'ils arrivent. Le prototype utilise les *Server-Sent Events* (SSE), une technique standard et légère. Comme il était hébergé sur Vercel, chaque connexion interrogeait la base toutes les 3 secondes. Sur notre propre serveur, PostgreSQL peut prévenir directement le serveur de chaque nouveau message (`LISTEN/NOTIFY`) : les messages arrivent instantanément, sans interroger la base en boucle.

**Ce qu'on en fait :**

- un **salon ouvert pendant les événements** : soirée alumni, JPO, webinaire ;
- « **qui est en ligne dans ma promo** », pour engager la conversation ;
- les **rencontres spontanées** entre membres connectés au même moment, pour un conseil, une offre ou un contact ;
- une modération complète : filtre, signalement, blocage d'un membre, historique consultable par l'administration.

## 5. Version mobile : une PWA

**Une seule base de code** : le site web devient une application installable (Progressive Web App). Le même site sert sur ordinateur et sur téléphone, sans passer par les stores.

- Icône sur l'écran d'accueil, plein écran, ouverture rapide.
- **Notifications mobiles** sur Android, et sur iPhone depuis iOS 16.4 une fois le site ajouté à l'écran d'accueil.
- **Partage natif** du téléphone (Web Share) vers WhatsApp, Instagram, TikTok ou SMS, sur chaque profil, offre, article et événement.
- **QR codes :**
  - carte de membre ;
  - inscription sur place lors d'une soirée alumni ou d'une JPO ;
  - pointage des présents.

Une présence dans les stores reste possible plus tard, en emballant la même PWA (Capacitor), sans réécrire.

## 6. Réseaux sociaux

Il faut distinguer ce que chaque plateforme permet réellement.

| Réseau | Ce qu'on fait | Condition |
|---|---|---|
| **Tous** | Bouton de partage natif ; aperçus Open Graph soignés (image, titre), pour que chaque lien partagé donne envie de cliquer | Aucune |
| **Instagram** | Publication croisée automatique des articles et événements vers le compte pro de l'école ; affichage des derniers posts de l'école sur l'accueil | Compte Instagram **professionnel** de l'école + application Meta (vérification de l'ENC) |
| **TikTok** | Intégration des vidéos de l'école sur l'accueil et dans les articles | Aucune pour l'intégration. La publication automatique exige un audit TikTok : sans audit, les vidéos postées par API restent privées |
| **WhatsApp** | Lien de **communauté WhatsApp** par filière ou par promo, affiché dans le groupe correspondant ; bouton « m'écrire sur WhatsApp » sur le profil, si le membre l'active | Aucune. L'envoi automatique de messages (API WhatsApp Business) est payant et demande une vérification Meta : à garder pour plus tard |
| **LinkedIn** | Connexion conservée ; bouton « partager sur LinkedIn » sur les offres et articles ; reprise du parcours par PDF (voir § 3) | L'API LinkedIn ne fournit pas le parcours aux applications ordinaires |

**Le levier réel n'est pas technique.** Les « gamins » sont sur Instagram, TikTok et WhatsApp. Le site doit donc :

- produire des contenus **faits pour être partagés là-bas** ;
- servir de **point d'arrivée** quand on clique.

Il faut un contenu qui vit (portraits d'alumni en vidéo courte, offres d'alternance, événements) et quelqu'un qui l'anime. Cela relève d'une décision de l'établissement, pas du code.

## 7. Priorités

| Quand | Quoi |
|---|---|
| Avant la bascule | Annuaire (§ 1), PWA de base (§ 4), partage natif et Open Graph, import CSV des étudiants |
| Avril - juin 2027 | Résumé hebdomadaire, profil pré-rempli par IA, Instagram, communautés WhatsApp, QR codes d'événements |
| Rentrée 2027 | Recherche en langage naturel, TikTok, notifications WhatsApp si le budget le permet |
