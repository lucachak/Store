from pathlib import Path
from decouple import config 
import os 

"""
MAIN CONFIG FILE, MEANING THAT ALL THE ACCOUNT, URL, TEMPLATE ETC... CONFIG ARE LOCATED HERE. 

SOME CONFIGS ARE PULLED FROM A .ENV 

CHANGED SOME LINES FROM THEME TO MATCH THE FOREST THEME FORM FROM ALLAUTH UI. 

LOCAL => VENDORS 

"""



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY') 
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

if DEBUG :
    ALLOWED_HOSTS = ['*']
else:
    pass






# Application definition

INSTALLED_APPS = [
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "unfold.contrib.import_export",  # optional, if django-import-export package is used
    "unfold.contrib.guardian",  # optional, if django-guardian package is used
    "unfold.contrib.simple_history",
    "crispy_forms",

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Internal Apps 
    'Home',
    'Auth',
    
    # External Apps
    "allauth_ui",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "widget_tweaks",
    "slippers",
    "django_browser_reload",

    "whitenoise.runserver_nostatic",
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    "whitenoise.middleware.WhiteNoiseMiddleware",

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    "allauth.account.middleware.AccountMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = 'Core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'Templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            "builtins": ["slippers.templatetags.slippers"],
        },
    },
]

WSGI_APPLICATION = 'Core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


        #'default': {
        #    'ENGINE': 'django.db.backends.mysql',
        #    'NAME': config('DATABASE_NAME', default=None, cast=str),
        #    'USER': config('DATABASE_USER', default=None, cast=str),
        #    'PASSWORD': config('DATABASE_PASSWD', default=None, cast=str),
        #    'HOST': config('DATABASE_HOST', default='localhost', cast=str),
        #    'PORT': config('DATABASE_PORT', default=3306, cast=str),
        #}
}

STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#   Django Allauth
SITE_ID = 1

ACCOUNT_SIGNUP_FIELDS = { 'email*', 'password1*', 'password2*'}
ACCOUNT_LOGIN_METHODS = {'email',}

ACCOUNT_EMAIL_VERIFICATION = "mandatory"

EMAIL_REQUIRED = True


LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SESSION_REMEMBER = True



ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[SaaS] "

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id':config('oauth_git_Cid'),
            'secret':config('oauth_git_Sec'),
        },
        'AUTH_PARAMS':{
            'prompt':'consent',
        },
        "VERIFIED_EMAIL":True,
    },



    'google':{
        'APP':{
            'client_id':config('GOOGLE_ID'),
            'secret':config('GOOGLE_SEC')
        },
        'VERIFIED_EMAIL':True,
    }
}

#   django allauth ui 
ALLAUTH_UI_THEME = "forest"


#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#email config
EMAIL_HOST = config('EMAIL_HOST',cast=str, default='smtp.gmail.com' )
EMAIL_PORT = config('EMAIL_PORT', cast=str, default='587')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool, default=False)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str, default=None)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str, default=None)

ADMINS=config('ADMINS', cast=list, default=None)
MANAGERS=ADMINS


# Django unfold
CRISPY_TEMPLATE_PACK = "unfold_crispy"

CRISPY_ALLOWED_TEMPLATE_PACKS = ["unfold_crispy"]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'Static/'
STATICFILES_BASE_DIR = BASE_DIR/"Static"
STATICFILES_VENDORS_DIR = STATICFILES_BASE_DIR/"Vendors"

STATICFILES_DIRS = [
    BASE_DIR/"Static",
]

STATIC_ROOT = BASE_DIR/"local-cdn"

MEDIA_ROOT =  os.path.join(BASE_DIR, 'Media')
MEDIA_URL = 'Media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
