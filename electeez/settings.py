import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
default = 'notsecretnotsecretnotsecretnotsecretnotsecretnotsecret'
SECRET_KEY = os.getenv('SECRET_KEY', default)
SECURE = SECRET_KEY != default
PROTO = os.getenv('PROTO', 'http')
HOST = os.getenv('HOST', 'localhost:8000')
BASE_URL = '://'.join([PROTO, HOST])

if SECURE:
    DEBUG = False
    ALLOWED_HOSTS = [os.getenv('HOST')]
else:
    DEBUG = True
    ALLOWED_HOSTS = ['*']

if DEBUG:
    os.environ['DJBLOCKCHAIN_MOCK'] = '1'

REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_REDIRECT_URL = '/'
USE_X_FORWARDED_HOST = True

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'electeez_auth.views.OTPBackend',
]

INSTALLED_APPS = [
    'sass_processor',
    'electeez',
    'electeez_auth',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djblockchain',
    'djcall',
    'djelectionguard',
    'djelectionguard_tezos',
    'django_registration',
    'django_extensions',
    'django_jinja',
    'channels',
    'ryzom',
    'ryzom_django',
    'ryzom_django_mdc',
    'django.forms'
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
    'ryzom_django.middleware.RyzomMiddleware',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'electeez.urls'

#RYZOM_APP = ''
#DDP_URLPATTERNS = 'electeez.routing'
#SERVER_METHODS = []
ASGI_APPLICATION = 'electeez.asgi.application'
#CHANNEL_LAYERS = {
#    "default": {
#        "BACKEND": "channels_redis.core.RedisChannelLayer",
#        "CONFIG": {
#            "hosts": [("localhost", 6379)]
#        },
#    },
#}

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'OPTIONS': {
            'environment': 'electeez.settings.jinja2',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
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
IPFS_ENABLED = 'IPFS_PATH' in os.environ or ipfs_home.exists()

WSGI_APPLICATION = 'electeez.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'PASSWORD': os.getenv('DB_PASS', None),
        'HOST': os.getenv('DB_HOST', None),
        'USER': os.getenv('DB_USER', None),
        'PORT': os.getenv('DB_PORT', None),
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'public'
STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
    'electeez.finders.StaticRootFinder',
]

if 'collectstatic' in sys.argv or not DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


EMAIL_HOST = os.getenv('EMAIL_HOST', None)
EMAIL_PORT = os.getenv('EMAIL_PORT', None)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', None)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', None)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@electeez.com')

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', BASE_DIR / 'media')

if 'ADMINS' in os.environ:
    ADMINS = [
        (email.split('@')[0], email)
        for email in os.getenv('ADMINS').split(',')
    ]

LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'log'))

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'formatters': {
        'timestamp': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO'),
        },
    },
    'loggers': {}
}

LOGGERS = (
    'django.request',
    'djcall',
    'djblockchain',
    'djblockchain.tezos',
    'daphne',
)

for logger in LOGGERS:
    LOGGING['loggers'][logger] = {
        'level': 'DEBUG',
        'handlers': ['console', logger + '.debug', logger + '.info', logger + '.error'],
        'propagate': True,
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
