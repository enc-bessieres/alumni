from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class MembreManager(BaseUserManager):
    """Crée les comptes : on se connecte avec son e-mail, sans identifiant."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        """
        Toute l'adresse en minuscules, sans espaces autour : Ines.Martin@Exemple.test et
        ines.martin@exemple.test sont la même personne. (Django ne met en minuscules que le
        domaine, après le @.)
        """
        return (email or "").strip().lower()

    def get_by_natural_key(self, email):
        # Utilisé par Django à la connexion : on retrouve le membre quelle que soit la casse saisie.
        return self.get(email__iexact=email)

    def create_user(self, email, password=None, **champs):
        if not email:
            raise ValueError("Un membre a forcément une adresse e-mail.")
        membre = self.model(email=self.normalize_email(email), **champs)
        membre.set_password(password)  # hache le mot de passe (pbkdf2_sha256) ; None = inutilisable
        membre.save(using=self._db)
        return membre

    def create_superuser(self, email, password=None, **champs):
        champs.update(
            is_superuser=True,
            role=Membre.Role.ADMINISTRATEUR,
            statut_inscription=Membre.StatutInscription.VALIDEE,
        )
        champs.setdefault("categorie", Membre.Categorie.ADMINISTRATIF)
        return self.create_user(email, password, **champs)


class Membre(AbstractBaseUser, PermissionsMixin):
    """
    Toute personne inscrite, quelle que soit sa catégorie. C'est aussi le compte de connexion
    de Django (AUTH_USER_MODEL) : AbstractBaseUser apporte le mot de passe haché et la date de
    dernière connexion, PermissionsMixin les groupes et les permissions.
    """

    class Civilite(models.TextChoices):
        MADAME = "madame", "Madame"
        MONSIEUR = "monsieur", "Monsieur"

    class Categorie(models.TextChoices):
        ALUMNI = "alumni", "Alumni"
        ETUDIANT = "etudiant", "Étudiant"
        ENSEIGNANT = "enseignant", "Enseignant"
        ADMINISTRATIF = "administratif", "Équipe administrative"
        CANDIDAT = "candidat", "Candidat"
        RECRUTEUR = "recruteur", "Recruteur"

    class StatutInscription(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        VALIDEE = "validee", "Validée"
        REFUSEE = "refusee", "Refusée"

    class Role(models.TextChoices):
        MEMBRE = "membre", "Membre"
        VALIDATEUR = "validateur", "Validateur"
        ADMINISTRATEUR = "administrateur", "Administrateur"

    # Identité
    civilite = models.CharField("civilité", max_length=10, choices=Civilite.choices, blank=True)
    prenom = models.CharField("prénom", max_length=150)
    nom = models.CharField("nom", max_length=150)
    nom_de_naissance = models.CharField("nom de naissance", max_length=150, blank=True)
    email = models.EmailField("e-mail", unique=True)

    categorie = models.CharField("catégorie", max_length=20, choices=Categorie.choices)
    statut_inscription = models.CharField(
        "statut de l'inscription",
        max_length=20,
        choices=StatutInscription.choices,
        default=StatutInscription.EN_ATTENTE,
    )
    role = models.CharField("rôle", max_length=20, choices=Role.choices, default=Role.MEMBRE)

    # Identifiant (UUID) chez Datalumni : import rejouable sans doublon, anciens liens redirigés.
    legacy_id = models.UUIDField(
        "identifiant Datalumni", null=True, blank=True, unique=True, editable=False
    )
    # Une valeur par défaut, et non auto_now_add : l'import pourra reprendre la date Datalumni.
    cree_le = models.DateTimeField("créé le", default=timezone.now)
    # La date de dernière connexion est le champ last_login d'AbstractBaseUser : Django le met
    # à jour à chaque connexion et s'en sert pour périmer les liens « mot de passe oublié ».

    # Utilisés par Django : compte actif, accès au back-office (déduit du rôle, voir save).
    is_active = models.BooleanField("actif", default=True)
    is_staff = models.BooleanField("accès au back-office", default=False)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["prenom", "nom"]

    objects = MembreManager()

    class Meta:
        verbose_name = "membre"
        ordering = ["nom", "prenom"]
        constraints = [
            # Filet de sécurité dans la base : même un import qui contourne save() (bulk_create)
            # ne peut pas créer deux comptes dont les e-mails ne diffèrent que par la casse.
            models.UniqueConstraint(Lower("email"), name="membre_email_unique_sans_casse"),
        ]
        # Permissions propres au projet, attribuées aux rôles dans membres/droits.py
        permissions = [
            ("consulter_annuaire", "Peut consulter l'annuaire"),
            ("valider_inscription", "Peut valider ou refuser une inscription"),
            ("changer_role", "Peut changer le rôle d'un membre"),
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def get_full_name(self):
        return str(self)

    def get_short_name(self):
        return self.prenom

    def clean(self):
        # Avant la vérification d'unicité des formulaires (back-office, inscription).
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def save(self, *args, **kwargs):
        # À chaque enregistrement, d'où qu'il vienne : formulaire, import, shell.
        self.email = self.__class__.objects.normalize_email(self.email)
        # L'accès au back-office découle du rôle : on ne le règle jamais à la main.
        self.is_staff = self.is_superuser or self.role != self.Role.MEMBRE
        super().save(*args, **kwargs)
