"""Réglages Django du projet Alumni ENC Bessières.

Toutes les valeurs propres à un poste ou à un serveur (secrets, base, e-mail)
viennent des variables d'environnement, définies dans le fichier .env.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Connexion, mot de passe oublié, puis Google et LinkedIn (django-allauth)
    "allauth",
    "allauth.account",
    "accueil",
    "membres",  # Alex : comptes, profils, annuaire
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

# En développement, les gabarits sont relus à chaque requête : une
# modification s'affiche sans redémarrer le serveur.
_LOADERS = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
if not DEBUG:
    _LOADERS = [("django.template.loaders.cached.Loader", _LOADERS)]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": _LOADERS,
        },
    },
]

ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# Le compte de connexion est notre modèle Membre (membres/models.py). Il doit être déclaré
# avant la première migration qui crée les tables de connexion : Django ne sait pas en changer
# ensuite. Les mots de passe sont hachés en pbkdf2_sha256, le format de Datalumni.
AUTH_USER_MODEL = "membres.Membre"

# --- Connexion avec django-allauth -----------------------------------------------------------
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "accueil:index"
# ModelBackend : le back-office de Django ; celui d'allauth : la connexion par e-mail du site.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_LOGIN_METHODS = {"email"}  # on se connecte avec son e-mail
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # notre Membre n'a pas d'identifiant
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
# Une adresse doit être vérifiée avant de se connecter. Les comptes importés de Datalumni
# arrivent avec une adresse déjà vérifiée : l'import crée la ligne EmailAddress correspondante.
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "membres.adapter.AdaptateurCompte"
# Mot de passe oublié : aucun e-mail n'est envoyé à une adresse qui n'est pas celle d'un membre.
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
# Le lien reçu par e-mail est valable une heure (Django le garde 3 jours par défaut).
PASSWORD_RESET_TIMEOUT = 60 * 60

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# E-mails : en développement, tout part dans Mailpit (http://localhost:8026).
EMAIL_HOST = os.environ.get("EMAIL_HOST", "mailpit")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "1025"))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "alumni@bessieres-alumni.org")
