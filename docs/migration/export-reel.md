# Les exports réels de Datalumni

Relevé du **25 novembre 2026**. Cette page décrit le format et les volumes des exports, sans aucune donnée personnelle. Les fichiers eux-mêmes sont dans le dépôt privé `enc-bessieres/alumni-donnees`, à cloner dans le dossier `sources/` du projet (`git clone https://github.com/enc-bessieres/alumni-donnees.git sources`). Ils ne vont jamais dans ce dépôt-ci, qui est public : voir `docs/decisions/0006-donnees-reelles.md`.

Elle remplace l'hypothèse de `docs/migration/export-factice.md`, qui supposait un fichier JSON.

## Les cinq fichiers

Tous les CSV sont en UTF-8 avec BOM (`utf-8-sig`), séparés par des virgules, avec une ligne d'en-tête.

| Fichier | Lignes | Contenu | Usage |
|---|---|---|---|
| `…_directory.csv` | 6138 | Un compte par ligne, 28 colonnes | **L'import principal** (Luc) |
| `…_jobs.csv` | 1 | Les offres non archivées, 19 colonnes | Modèle des offres (Vera) |
| `…_job_applications.csv` | 66 | Les candidatures, sur 29 offres, 17 colonnes | Modèle des candidatures (Vera) |
| `…_mentoring_pairs.csv` | 6 | Les relations de mentorat, 14 colonnes | Pas d'import : trop peu de lignes |
| `…_france_competences.xlsx` | 6314 | Enquête d'insertion professionnelle | Hors du site ; conservé par l'établissement |

Les offres archivées s'exportent à part et ne sont pas encore là : 28 des 29 offres citées par les candidatures manquent.

## L'annuaire : `directory.csv`

### Le chiffre à retenir

| | Comptes |
|---|---|
| Total | **6138** |
| Activés (`account_status` = `True`) | **1233** |
| Jamais activés | 4905 |

Les 1214 membres relevés par l'audit étaient les comptes activés : ce sont les seuls que Datalumni montre dans l'annuaire. Les autres ont été importés en masse (4601 en avril 2025, 715 en octobre 2025) et n'ont jamais servi.

### Les colonnes

| Colonne | Remplie | Contenu et remarques |
|---|---|---|
| `user_id` | 6138 | UUID, unique : devient `legacy_id` |
| `external_ref` | 0 | Toujours vide |
| `first_name` | 6134 | 4 comptes sans prénom ni nom |
| `last_name` | 6134 | **En majuscules** pour 6036 comptes |
| `birth_name` | 55 | |
| `email` | 6138 | Unique, déjà en minuscules |
| `civility` | 1242 | 5 écritures : `Mme.`, `M.`, `Madame`, `Monsieur`, `Non renseigné` |
| `location` | 663 | Nom de ville, en texte ; pas de coordonnées |
| `phone` | 996 | Format international (`+33…`) |
| `account_status` | 6138 | `True` = compte activé |
| `current_position` | 357 | Intitulé du poste actuel |
| `current_company` | 357 | |
| `business_sector` | 340 | 26 valeurs (liste ci-dessous) |
| `last_login` | 1252 | Date ISO avec fuseau |
| `last_profile_update` | 5744 | Date ISO avec fuseau |
| `account_activation_date` | 1233 | Date seule ; remplie pour les comptes activés |
| `category` | 6133 | 6 catégories, parfois deux séparées par ` / ` |
| `campus` | 4978 | 2 sites, parfois les deux séparés par ` / ` |
| `degree` | 5701 | 20 diplômes, parfois deux ou trois séparés par ` / ` |
| `promotion_year` | 5691 | **Une seule année**, de 1963 à 2029 |
| `import_date` | 5683 | Vide = le membre s'est inscrit seul (455 comptes) |
| `notifications_newsletter` | 6128 | `True` pour 300 comptes |
| `notifications_event` | 6118 | `True` pour 5788 comptes |
| `notifications_registration` | 6118 | `True` pour 5779 comptes |
| `visibility_recruiters` | 6129 | `True` pour 642 comptes |
| `visibility_directory` | 6129 | **Toujours `True`** |
| `job_search` | 289 | `True` pour 283 comptes |
| `mentoring_role` | 282 | `mentor` (166), `mentee` (103), `mentor / mentee` (13) |

### Les catégories

| Catégorie | Tous les comptes | Comptes activés |
|---|---|---|
| Alumni | 5677 | 1143 |
| Recruteur | 336 | 17 |
| Enseignant | 79 | 43 |
| Candidat | 16 | 8 |
| Étudiant | 9 | 9 |
| Équipe administrative | 4 | 4 |
| Deux catégories (`Enseignant / Équipe administrative`, `Alumni / Recruteur`, `Alumni / Candidat`) | 12 | 9 |
| Vide | 5 | 0 |

### Les cas à traiter dans l'import

| Cas | Volume | Ce qu'il faut décider ou faire |
|---|---|---|
| **Plusieurs diplômes, une seule promo** : `BTS CG / DCG` avec une année | 121 comptes | L'export ne dit pas à quel diplôme appartient l'année. À décider : l'attribuer au dernier diplôme, ou laisser la promo vide pour les autres |
| **Diplômes en majuscules** : `BTS ASSURANCE`, `BTS COMMUNICATION` | Tous | Table de correspondance avec les diplômes du référentiel, testée sur les 20 |
| **Deux sites** : `ENC Bessières / ENC Bessières Apprentissage` | 52 comptes | Même question que pour les diplômes |
| **Deux catégories** | 12 comptes | Notre modèle n'en porte qu'une : choisir une règle de priorité |
| **Sans diplôme** | 437 comptes | Surtout des recruteurs et des enseignants : normal |
| **Sans site** | 1160 comptes | Import sans site |
| **Sans catégorie, ou sans nom** | 5 et 4 comptes | À lister dans le rapport d'import, sans bloquer |
| **Noms en majuscules** | 6036 comptes | À décider : les garder, ou les passer en « Dupont » (attention aux noms composés et aux particules) |
| **Civilité** | 5 écritures | Ramener à nos valeurs ; `Non renseigné` devient vide |
| **Homonymes** : même prénom et même nom | 128 groupes, 259 comptes | Rapport de doublons possibles ; fusion à la main |
| **Comptes jamais activés** | 4905 comptes | Importés, mais **absents de l'annuaire** tant que le compte n'est pas activé |
| **Adresses `enc-bessieres.org`** | 2048 comptes | Peut-être des adresses d'étudiants fermées après le diplôme : à vérifier avant tout envoi |

### Les secteurs d'activité

Les 26 valeurs de `business_sector`, pour le référentiel des secteurs (#39) : Agences de communication, marketing, événementiel · Agro-alimentaire · Association non lucrative · Automobile · Autres · Banque / Assurance / Finance · Cabinet d'expertise comptable / Comptabilité · Conseil / Audit · Culture / Media / Divertissement · Digital / Technologie · Droit / Eco-gestion / Science Politique · Enseignement / Formation / Recrutement · Enseignement, Formation · Entrepreneuriat / Start-up · Environnement / Santé / Social · Esthétique · Grande distribution / Ventes · Hôtellerie · Industrie · Mode / Luxe / Beauté · Organisation internationale · Publicité / Marketing / Communication · Sciences / Recherche · Secteur public et administration · Tourisme / Hôtellerie / Restauration · Travaux Publics.

Attention : une valeur contient elle-même ` / ` (« Conseil / Audit »). Ce séparateur ne se découpe donc que dans `category`, `campus` et `degree`.

## Les offres et les candidatures

| Colonne des offres (`jobs.csv`) | Remarque |
|---|---|
| Titre, Entreprise, Localisation, Auteur | Texte |
| Type | Type de contrat : `CDI`, `Alternance`, `Stage`, `CDD`, `Autre` |
| Secteur | La même liste que `business_sector` |
| Rémunération | Une **tranche**, pas un montant : `< 15k €`, `Stage non-indemnisé`, `Non renseigné` |
| Date publication, Date de début, Dès que possible | |
| Statut, Archivage, Raison de refus | `APPROVED` ; `NOT_ARCHIVED` |
| Lien candidature, Email candidature, Nom du contact | Trois façons de postuler |
| Vues, Lien, Intégration | |

Les candidatures portent un mode (`Sur la plateforme`, `Lien externe`, `Par email`), le candidat, la date, l'offre visée et, pour 49 d'entre elles, un lien vers une pièce jointe hébergée chez Datalumni.

## Ce que les exports ne contiennent pas

| Absent | Conséquence |
|---|---|
| **Mots de passe**, même hachés | Voir ci-dessous |
| Comptes Google ou LinkedIn rattachés | Le rattachement se fait par l'adresse e-mail vérifiée |
| Parcours complet (expériences passées, formations) | Seul le poste actuel est repris, pour 357 membres |
| Photos, CV, résumé, compétences, liens | À demander à Datalumni, ou à ressaisir par le membre |
| Date d'acceptation des CGU | Les membres acceptent les CGU de l'ENC à leur première connexion |
| Statut de l'inscription (en attente, refusée) | Un compte activé est considéré comme validé |
| Articles, événements, groupes, messages | 14 articles et 2 événements : reprise à la main |

## Les mots de passe et la première connexion

Datalumni ne fournit pas les mots de passe. La vérification de l'ancien mot de passe au premier login, prévue dans `docs/06-points-durs.md`, est abandonnée. Tous les comptes sont importés **sans mot de passe utilisable** (`set_unusable_password()`).

L'export dit en revanche qui s'était inscrit : c'est la colonne `account_status`. L'import la conserve sur le membre, et le site s'en sert pour adapter ce qu'il dit, sans jamais expliquer pourquoi.

### Trois situations

| Situation | Comment le site la reconnaît | Comptes | Ce qu'on dit au membre |
|---|---|---|---|
| **Déjà inscrit chez Datalumni** | `account_status` = `True` à l'import, et pas encore de mot de passe ici | 1233 | « Modifiez votre mot de passe » |
| **Jamais inscrit** : compte importé par l'école, jamais activé | `account_status` = `False` à l'import, et pas encore de mot de passe ici | 4905 | « Définissez votre mot de passe » |
| **Déjà passé par le nouveau site**, ou inscrit ici | Le compte a un mot de passe | 0 au départ | Connexion ordinaire |

### Le parcours

1. **La connexion commence par l'adresse e-mail seule.** Un champ, un bouton « Continuer ».
2. **Le compte a un mot de passe :** le site demande le mot de passe. C'est aussi ce qu'il affiche pour une adresse inconnue, qui échouera comme un mauvais mot de passe.
3. **Le compte est importé et n'a pas encore de mot de passe :** le site envoie un lien à cette adresse et l'annonce, avec le texte de la situation :
   - déjà inscrit : « Pour continuer, modifiez votre mot de passe. Nous venons de vous envoyer un lien à cette adresse. » ;
   - jamais inscrit : « Bienvenue ! Pour activer votre compte, définissez votre mot de passe. Nous venons de vous envoyer un lien à cette adresse. »
4. **L'e-mail et la page ouverte par le lien** portent le même mot : « Modifier mon mot de passe » ou « Définir mon mot de passe ». La page demande le nouveau mot de passe, deux fois. Elle ne demande **jamais l'ancien**.
5. **Une fois le mot de passe enregistré,** le membre est connecté, son adresse est marquée vérifiée, et son compte est activé : il entre dans le cas « connexion ordinaire » pour la suite.

### Ce qui protège les comptes

- **Le mot de passe ne se définit que par le lien reçu par e-mail.** Sans accès à la boîte du membre, on ne peut pas prendre son compte. Il n'existe aucune page qui permette de le définir directement.
- **Le lien ne sert qu'une fois et expire** (jeton de réinitialisation de Django, `PASSWORD_RESET_TIMEOUT`). Un bouton « Renvoyer le lien » en redemande un.
- **Le nombre d'envois est limité** par adresse e-mail et par adresse IP, pour qu'on ne puisse ni inonder une boîte, ni tester des adresses en série.
- **Un compte jamais activé reste hors de l'annuaire** jusqu'à ce que son titulaire ait défini son mot de passe.

### À décider

- **Le membre qui n'a plus accès à son adresse** (ancienne adresse d'étudiant, ancien employeur) : il ne peut pas recevoir le lien. Il lui faut une façon de joindre l'équipe, qui change l'adresse dans le back-office après vérification.
- **Un e-mail d'annonce à la bascule,** aux 1233 inscrits ou à tous : le parcours ci-dessus fonctionne sans, puisque le lien part quand le membre se présente.
- **« Se connecter avec Google »** évite le mot de passe pour les 2724 adresses Gmail.

## Tester les performances

Le générateur d'export factice doit produire **le même CSV** : mêmes colonnes, 6138 lignes, mêmes proportions (20 % de comptes activés, 2 % de diplômes multiples, noms en majuscules). Les tests et l'intégration continue s'appuient sur lui, jamais sur les fichiers réels.
