# Points durs de l'intégration — à anticiper

Ces sujets sont difficiles parce qu'ils touchent les vraies données, de vrais comptes, des services extérieurs ou le domaine. Le principe est le même pour tous :

- **les étudiants construisent le mécanisme avec des données et des services de test** ;
- **Philippe Chenut** (DDFPT) obtient tout ce qui dépend de Datalumni et de l'établissement : accès administrateur, export, domaine, page LinkedIn, DPO ;
- **Timothée le branche sur le réel** (vraies données, comptes de production, DNS, envoi d'e-mails).

Ainsi rien ne bloque pendant le stage, et rien de sensible ne passe par les postes des étudiants.

## 1. Les comptes et les mots de passe

### Ce qui se passe

Les comptes Datalumni vivent dans **Authentik**, qui stocke les mots de passe au format Django :

```text
pbkdf2_sha256$<itérations>$<sel>$<empreinte>
```

Si Datalumni fournit ce champ, on peut vérifier l'ancien mot de passe au premier login, puis le ré-enregistrer au format du nouveau site. Le membre ne s'aperçoit de rien.

### Les cas difficiles

| Cas | Volume probable | Traitement |
|---|---|---|
| **Comptes importés jamais activés** : le mot de passe est vide ou inutilisable | Une bonne part des **784 comptes importés** en avril 2025 | Pas de mot de passe à reprendre : le membre reçoit un **lien d'activation** par e-mail |
| **Comptes Google ou LinkedIn seulement**, sans mot de passe | Inconnu (à demander dans l'export) | Reconnexion par Google ou LinkedIn (voir § 2), sinon « mot de passe oublié » |
| **Doublons** : même personne importée puis inscrite elle-même, avec deux e-mails | Quelques dizaines probablement | Rapport de doublons (même nom + même diplôme), **fusion manuelle** par Timothée |
| **E-mails morts** : adresses d'élève ou d'ancien employeur | Fréquent chez des anciens | Rejets lors de l'envoi d'annonce ; le compte reste, en attente d'une reconnexion |
| **Comptes en attente de validation ou refusés** | Quelques-uns | Importés avec leur statut |
| **Membres masqués de l'annuaire** : l'API membre en montre 1214, le total réel est plus élevé | Inconnu | L'export doit contenir **tous** les comptes, pas seulement les visibles |
| **CGU** : les membres ont accepté celles de Datalumni | Tous | Nouvelles CGU de l'ENC à **accepter au premier login** |

### Règles pour l'import

- **Garder l'identifiant Datalumni** (UUID) dans une colonne `legacy_id`. Cela sert à deux choses :
  - les anciens liens `/profile/<uuid>` continuent de fonctionner, par redirection ;
  - l'import peut être **rejoué** sans créer de doublons, ce qui est indispensable pour les migrations à blanc.
- L'import ne doit jamais écraser un compte déjà actif sur le nouveau site.

### Répartition

- **Étudiants (Axel, Luc) :**
  - le vérificateur `pbkdf2_sha256` et la ré-écriture du mot de passe au login, testés avec des empreintes générées pour l'occasion ;
  - le lien d'activation ;
  - l'import rejouable avec `legacy_id` ;
  - le rapport de doublons.
- **Philippe :** obtenir les vraies empreintes auprès de Datalumni.
- **Timothée :** lancer l'import réel, trancher les doublons.

## 2. Google et LinkedIn

### Ce qui se passe

Les applications Google et LinkedIn actuelles appartiennent à Datalumni. **Il faut créer celles de l'ENC.** Le membre qui clique sur « Se connecter avec Google » est rattaché à son compte importé :

- **par son identifiant Google**, si Datalumni l'exporte : Authentik le conserve dans les liaisons de sources ;
- **sinon par son e-mail vérifié**.

### Les cas difficiles

| Sujet | Difficulté | Traitement |
|---|---|---|
| **Application Google** | Écran de consentement à configurer et à **publier** : en mode « test », il est limité à 100 utilisateurs déclarés | Projet Google Cloud de l'ENC ; uniquement `openid email profile`, qui ne demande pas d'audit Google |
| **Application LinkedIn** | Elle doit être **associée à une page LinkedIn** et validée par un administrateur de cette page | Page « ENC Bessières » : identifier qui en est administrateur |
| **E-mail Google différent de l'e-mail du compte** | Le rapprochement par e-mail échoue, et un **doublon** se crée | Ne jamais créer de compte automatiquement à la connexion Google d'un ancien membre ; proposer « J'ai déjà un compte » puis un lien par e-mail ; bouton « lier mon compte Google » dans les paramètres |
| **Identifiant LinkedIn** | On ne sait pas s'il est identique d'une application à l'autre | À vérifier ; à défaut, rapprochement par e-mail |
| **Adresses de retour** (*redirect URI*) | Elles doivent être déclarées exactement, pour chaque environnement | Une application « dev » (localhost) et une application « production » |

### Répartition

- **Étudiant (Axel) :** connexion Google et LinkedIn avec les identifiants **de développement** fournis par Timothée, rattachement, liaison et déliaison dans les paramètres.
- **Philippe :** identifier l'administrateur de la page LinkedIn de l'école.
- **Timothée :** créer les applications de l'ENC (dev et production), publier l'écran de consentement Google.

## 3. L'envoi d'e-mails

### Ce qui se passe

Le site envoie trois sortes d'e-mails :

- les messages **automatiques** : activation, mot de passe, notifications ;
- les **envois groupés** : newsletter, annonce de la bascule ;
- les **résumés hebdomadaires**, plus tard.

Le jour de la bascule, **plus de 1214 membres** doivent recevoir leur lien.

### Les cas difficiles

| Sujet | Difficulté | Traitement |
|---|---|---|
| **Être reçu, pas classé en spam** | Il faut les enregistrements DNS **SPF, DKIM et DMARC** sur `bessieres-alumni.org` | Nécessite le contrôle du DNS, donc la propriété du domaine |
| **Prestataire d'envoi** | Le Microsoft 365 de l'ENC n'est pas fait pour les envois en masse (débit limité, aucune gestion des désinscriptions) | Un service d'e-mail transactionnel. Datalumni utilise déjà Brevo. L'offre gratuite (300/jour) ne suffit pas pour la bascule, une petite offre payante le temps de l'opération suffit |
| **Désinscription** | Obligatoire pour la newsletter | Lien dans chaque envoi groupé, préférence respectée |
| **Rejets** | Adresses mortes | Marquer l'adresse invalide, ne plus y écrire |

### Répartition

- **Étudiants (Luc) :**
  - les modèles d'e-mails ;
  - l'envoi via la couche e-mail du framework ;
  - la désinscription ;
  - l'envoi par lots.
  - En développement, **tout part dans Mailpit**, et rien ne sort réellement.
- **Timothée :** compte chez le prestataire, DNS (SPF, DKIM, DMARC), envoi réel de l'annonce.

## 4. Les fichiers

- **Photos (296), CV, images d'articles** : ils sont aujourd'hui servis par `media3.datalumni.com`. Il faut les **télécharger avant la fin du contrat**, de préférence les originaux fournis par Datalumni.
- **Étudiant (Luc) :** script de rapatriement qui relie chaque fichier à son membre ou son article.
- **Timothée :** l'exécuter sur le réel.

## 5. Les localisations

Les villes sont géocodées (latitude, longitude, commune, département, région, pays). Pour les nouvelles saisies, on utilise la **Base Adresse Nationale** (`api-adresse.data.gouv.fr`), gratuite et sans clé, pour la France. Pour l'étranger, on utilise **Nominatim** (OpenStreetMap), limité à 1 requête par seconde. Les étudiants s'en chargent pendant le stage, sans prérequis.

## 6. Le domaine et la bascule

| Sujet | Action | Qui |
|---|---|---|
| **Propriété du domaine** | Savoir quel compte OVH le détient (ENC ou Datalumni). Il **expire le 25 mars 2027** | Philippe, **tout de suite** |
| **Bascule DNS** | Réduire la durée de cache (TTL) quelques jours avant, puis faire pointer le domaine vers le nouveau serveur | Timothée |
| **Certificat HTTPS** | Let's Encrypt automatique sur le nouveau serveur | Timothée |
| **Anciens liens** | Rediriger `/profile/<uuid>`, `/blog/<slug>` et `/directory` vers les nouvelles adresses | Étudiants, avec `legacy_id` |
| **Hébergement de production** | Demandé au prestataire de l'ENC : serveur Linux avec Docker, accès SSH, hébergement dans l'UE, sauvegardes quotidiennes hors du serveur, disponible mi-janvier | Philippe demande, Timothée installe |
| **Fenêtre de bascule** | Datalumni en lecture seule, dernier export, import, vérifications, ouverture | Timothée, un soir ou un week-end |

## 7. RGPD

- Les nouvelles **CGU et politique de confidentialité** de l'ENC remplacent celles de Datalumni.
- Il faut **informer les membres** du changement de plateforme, dans l'annonce de la bascule.
- Il faut **prévenir le DPO** de l'établissement, et inscrire le traitement à son registre (Philippe).
- On ne met **pas de traceur publicitaire**. Pour les statistiques, il y a deux voies : aucune, ou un outil sans cookie hébergé par l'ENC.
- **Aucune donnée réelle sur les postes des étudiants.** Ils travaillent sur des données anonymisées que Timothée produit à partir de l'export.

## 8. Ce qu'il faut demander à Datalumni

Datalumni s'est engagé à fournir les données. Philippe leur envoie cette liste, pour éviter un export incomplet découvert en mars. Il demande **un échantillon tout de suite**, l'export complet ensuite, et en premier lieu **un accès administrateur** à la plateforme, pour voir tout le contenu.

1. **Format** : JSON ou CSV, avec la description de chaque champ.
2. **Tous les comptes**, y compris ceux masqués de l'annuaire, en attente, refusés ou désactivés, avec leur identifiant (UUID).
3. **Les mots de passe** : le champ `password` d'Authentik, tel quel (`pbkdf2_sha256$…`), avec la date de dernière connexion.
4. **Les liaisons Google et LinkedIn** : pour chaque compte, le fournisseur et l'identifiant (`sub`).
5. **Les profils complets** :
   - identité, localisation géocodée ;
   - expériences, formations, compétences, centres d'intérêt, liens ;
   - préférences de visibilité, de notification et de mentorat ;
   - recherche d'opportunité, tags.
6. **Les groupes** : sites, niveaux, diplômes, clubs, et l'appartenance de chaque membre avec son année de promotion.
7. **Les contenus** : articles du blog, posts, commentaires, événements et inscrits, offres, ressources, pages.
8. **Les relations** : messages privés, relations de mentorat.
9. **Les fichiers** : photos, CV, images et documents en **originaux**, avec leur rattachement.
10. **Les réponses aux questionnaires** (inscription, enquête d'insertion), si elles sont utilisées.
11. **Les consentements** : date d'acceptation des CGU, abonnement à la newsletter.
12. **Le calendrier** : date de l'échantillon, de l'export complet, et possibilité d'un **dernier export le jour de la bascule**.
