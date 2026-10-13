"""
Project settings.

Everything environment-specific comes from the environment (or a local `.env`
file, see `env.example`). Nothing secret lives in this file.

Project conventions
-------------------
* Templates live in `Templates/`. One folder per app, shared pieces in
  `Templates/Components/`, django-allauth overrides in `Templates/allauth/`
  and `Templates/account/`.
* Class-based views, camelCase class names, kebab-case URL paths.
* Every user-facing string goes through `{% trans %}` / `gettext`, and the
  translations live in `locale/`.
"""
import sys
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
TESTING = "test" in sys.argv

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Public origin of the site, used to build Stripe return URLs.
BASE_URL = config("BASE_URL", default="http://localhost:8000").rstrip("/")
SITE_NAME = config("SITE_NAME", default="Tally")

# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
INSTALLED_APPS = [
    "unfold",  # must come before django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Internal apps
    "Home",
    "Auth",
    "Subscription",
    "Customers",
    "Checkout",
    # External apps
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "widget_tweaks",
    "whitenoise.runserver_nostatic",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Needs request.user, so it has to come after authentication.
    "Auth.middleware.IdleLogoutMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("django_browser_reload")
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

ROOT_URLCONF = "Core.urls"
WSGI_APPLICATION = "Core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "Templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "Core.context_processors.site",
            ],
        },
    },
]

# --------------------------------------------------------------------------- #
# Database (PostgreSQL by default, see env.example)
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=config("DATABASE_CONN_MAX_AGE", default=60, cast=int),
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
# Authentication (django-allauth)
# --------------------------------------------------------------------------- #
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "dashboard"
ACCOUNT_LOGOUT_REDIRECT_URL = "home"

ACCOUNT_LOGIN_METHODS = {"email"}
# A list, not a set: the order of this setting decides the order of the form.
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_SUBJECT_PREFIX = f"[{SITE_NAME}] "
ACCOUNT_SESSION_REMEMBER = None  # ask on the login form
ACCOUNT_LOGIN_BY_CODE_ENABLED = False

# Two-factor authentication (TOTP apps such as Google Authenticator).
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
MFA_TOTP_ISSUER = SITE_NAME

SOCIALACCOUNT_LOGIN_ON_GET = False


def _social_app(prefix: str, *legacy_names: str) -> dict:
    """Return the allauth `APP` config for a provider, or {} when not configured."""
    legacy_id, legacy_secret = legacy_names or ("", "")
    client_id = config(f"{prefix}_CLIENT_ID", default=config(legacy_id, default="") if legacy_id else "")
    secret = config(f"{prefix}_CLIENT_SECRET", default=config(legacy_secret, default="") if legacy_secret else "")
    if client_id and secret:
        return {"APP": {"client_id": client_id, "secret": secret}}
    return {}


# A provider is only offered on the login page when its credentials are set.
SOCIALACCOUNT_PROVIDERS = {}
if _github := _social_app("GITHUB", "oauth_git_Cid", "oauth_git_Sec"):
    SOCIALACCOUNT_PROVIDERS["github"] = {**_github, "VERIFIED_EMAIL": True, "SCOPE": ["user:email"]}
if _google := _social_app("GOOGLE", "GOOGLE_ID", "GOOGLE_SEC"):
    SOCIALACCOUNT_PROVIDERS["google"] = {**_google, "VERIFIED_EMAIL": True, "SCOPE": ["profile", "email"]}

# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=60 * 60 * 24 * 14, cast=int)
# Seconds of inactivity before a signed-in user is logged out. 0 disables it.
SESSION_IDLE_TIMEOUT = config("SESSION_IDLE_TIMEOUT", default=60 * 60 * 2, cast=int)

# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "noreply@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --------------------------------------------------------------------------- #
# Stripe / billing
# --------------------------------------------------------------------------- #
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
BILLING_CURRENCY = config("BILLING_CURRENCY", default="usd").lower()

if not DEBUG and not TESTING and STRIPE_SECRET_KEY.startswith("sk_test"):
    raise ImproperlyConfigured("A Stripe test key is configured while DEBUG is off.")

# --------------------------------------------------------------------------- #
# Internationalisation
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("pt-br", "Português (Brasil)"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# Static and media files
# --------------------------------------------------------------------------- #
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "Static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "Media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        # The manifest storage needs `collectstatic`, which tests and local dev don't run.
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage"
            if DEBUG or TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
WHITENOISE_USE_FINDERS = DEBUG

# --------------------------------------------------------------------------- #
# Admin (django-unfold)
# --------------------------------------------------------------------------- #
UNFOLD = {
    "SITE_TITLE": SITE_NAME,
    "SITE_HEADER": SITE_NAME,
    "SITE_URL": "/",
}

# --------------------------------------------------------------------------- #
# Production hardening
# --------------------------------------------------------------------------- #
if not DEBUG:
    if config("BEHIND_PROXY", default=False, cast=bool):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

ADMINS = [tuple(pair.split(":", 1)) for pair in config("ADMINS", default="", cast=Csv()) if ":" in pair]
MANAGERS = ADMINS
