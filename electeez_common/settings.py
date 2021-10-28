import os
from pathlib import Path
import sys
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

HOST = os.getenv('HOST')
ENVIRONMENT = os.getenv('CI_ENVIRONMENT_NAME', 'localhost')

# SECURITY WARNING: keep the secret key used in production secret!
default = 'notsecretnotsecretnotsecretnotsecretnotsecretnotsecret'
SECRET_KEY = os.getenv('SECRET_KEY', default)
SECURE = SECRET_KEY != default
PROTO = os.getenv('PROTO', 'http')
HOST = os.getenv('HOST', 'localhost:8000')
BASE_URL = '://'.join([PROTO, HOST])


DEBUG = ENVIRONMENT == 'localhost'
DEBUG = os.getenv('DEBUG', DEBUG)

if SECURE:
    if not HOST.startswith('www'):
        HOST = 'www.' + HOST
    DEBUG = False
    ALLOWED_HOSTS = [HOST]
else:
    ALLOWED_HOSTS = ['*']


if DEBUG:
    os.environ['DJBLOCKCHAIN_MOCK'] = '1'

REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_REDIRECT_URL = '/'
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    'sass_processor',
    'electeez_common',
    'electeez_auth',
    'django.contrib.admin',
    'django.contrib.sites',
    'electeez_sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djtezos',
    'djcall',
    'djlang',
    'djelectionguard',
    'djelectionguard_tezos',
    'djelectionguard_tracker',
    'django_registration',
    'django_extensions',
    'django_jinja',
    'channels',
    'django.forms',
    'ryzom',
    'py2js',
    'ryzom_django',
    'ryzom_django_mdc',
    'social_django',
    'baloti_auth',
]

AUTH_USER_MODEL = 'electeez_auth.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'electeez_common.urls'

#RYZOM_APP = ''
#DDP_URLPATTERNS = 'electeez.routing'
#SERVER_METHODS = []
ASGI_APPLICATION = 'electeez_common.asgi.application'
#CHANNEL_LAYERS = {
#    "default": {
#        "BACKEND": "channels_redis.core.RedisChannelLayer",
#        "CONFIG": {
#            "hosts": [("localhost", 6379)]
#        },
#    },
#}

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        release=os.getenv('CI_COMMIT_SHA'),
        integrations=[DjangoIntegration()],
        attach_stacktrace=True,
        send_default_pii=True
    )

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'OPTIONS': {
            'environment': 'electeez_common.settings.jinja2',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

RYZOM_TEMPLATE_BACKEND = {
    "BACKEND": "ryzom_django.template_backend.Ryzom",
    "OPTIONS": {
        "app_dirname": "components",
        "components_module": "ryzom.components.muicss",
        "components_prefix": "Mui",
        # "components_module": "ryzom.components.django",
        # "components_prefix": "Django",

        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.i18n",
        ],
        # "autoescape": True,
        # "auto_reload": DEBUG,
        # "translation_engine": "django.utils.translation",
        # "debug": False,
    }
}
TEMPLATES.insert(0, RYZOM_TEMPLATE_BACKEND)  # noqa: F405

def jinja2(**options):
    from django.templatetags.static import static
    from django.urls import reverse
    from jinja2 import Environment
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        'len': len,
        'PROTO': os.getenv('PROTO', 'http'),
    })
    return env

DJBLOCKCHAIN = dict(
    TEZOS_CONTRACTS='djelectionguard_tezos/tezos',
)

ipfs_home = Path(os.getenv('HOME')) / '.ipfs'
IPFS_ENABLED = 'IPFS_URL' in os.environ or ipfs_home.exists()
IPFS_URL = os.getenv('IPFS_URL', 'localhost:5001')

WSGI_APPLICATION = 'electeez_common.wsgi.application'

MEMCACHED_HOST = os.getenv('MEMCACHED_HOST', 'localhost')

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []
else:
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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

EMAIL_HOST = os.getenv('EMAIL_HOST', None)
EMAIL_PORT = os.getenv('EMAIL_PORT', None)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', None)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', None)

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    # EMAIL_FILE_PATH = '/tmp/app-messages' # change this to a proper location


MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')

ADMINS_EMAIL = []

if 'ADMINS' in os.environ:
    ADMINS = [
        (email.split('@')[0], email)
        for email in os.getenv('ADMINS').split(',')
    ]
    ADMINS_EMAIL = [email for email in os.getenv('ADMINS').split(',')]

LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'log'))

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'formatters': {
        'timestamp': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'loggers': {},
}

LOGGERS = (
    'django.request',
    'djcall',
    'daphne',
    'electionguard'
)

for logger in LOGGERS:
    LOGGING['loggers'][logger] = {
        'level': 'DEBUG',
        'handlers': ['console', logger + '.debug', logger + '.info', logger + '.error'],
    }
    LOGGING['handlers'][logger + '.debug'] = {
        'level': 'DEBUG',
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': LOG_DIR + f'/{logger}.debug.log',
        'formatter': 'timestamp'
    }
    LOGGING['handlers'][logger + '.info'] = {
        'level': 'INFO',
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': LOG_DIR + f'/{logger}.info.log',
        'formatter': 'timestamp'
    }
    LOGGING['handlers'][logger + '.error'] = {
        'level': 'ERROR',
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': LOG_DIR + f'/{logger}.error.log',
        'formatter': 'timestamp'
    }


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
    'electeez_common.finders.StaticRootFinder',
]

if 'collectstatic' in sys.argv or not DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

AUTHENTICATION_BACKENDS = [
    'social_core.backends.linkedin.LinkedinOAuth2',
    'social_core.backends.instagram.InstagramOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# LOGIN_URL = 'login'
# LOGIN_REDIRECT_URL = 'home'
# LOGOUT_URL = 'logout'
# LOGOUT_REDIRECT_URL = 'login'

SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('SOCIAL_AUTH_FACEBOOK_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('SOCIAL_AUTH_FACEBOOK_SECRET')
