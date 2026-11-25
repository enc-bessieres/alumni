# Les exports réels de Datalumni

Relevé du **25 novembre 2026**. Cette page décrit le format et les volumes des exports, sans aucune donnée personnelle. Les fichiers eux-mêmes sont dans le dossier `sources/` de chaque poste et ne vont jamais dans le dépôt : voir `docs/decisions/0006-donnees-reelles.md`.

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

## Les mots de passe

Datalumni ne fournit pas les mots de passe. La vérification de l'ancien mot de passe au premier login, prévue dans `docs/06-points-durs.md`, est abandonnée.

- **Tous les comptes sont importés sans mot de passe utilisable** (`set_unusable_password()`).
- **À la première connexion**, le membre demande un lien par e-mail et définit son mot de passe. C'est le parcours « mot de passe oublié », déjà livré : il reste à l'annoncer clairement sur la page de connexion.
- **Le lien prouve que l'adresse appartient au membre** : elle est marquée vérifiée au même moment, et un compte jamais activé devient activé.
- **« Se connecter avec Google »** évite le mot de passe pour les adresses Gmail : 2724 comptes.
- Pour 4905 comptes sur 6138, il n'y avait de toute façon aucun mot de passe à reprendre.

## Tester les performances

Le générateur d'export factice doit produire **le même CSV** : mêmes colonnes, 6138 lignes, mêmes proportions (20 % de comptes activés, 2 % de diplômes multiples, noms en majuscules). Les tests et l'intégration continue s'appuient sur lui, jamais sur les fichiers réels.
