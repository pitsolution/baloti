from django.utils.translation import gettext_lazy as _

from electeez_common.settings import *

SITE_ID = 1
SITE_NAME = 'electis'

INSTALLED_APPS += ['electis']

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('fr', _('French')),
    ('en', _('English'))
)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'public'
STATICFILES_DIRS = [
    BASE_DIR / 'electis' / 'static',
    BASE_DIR / 'static',
]

if DEBUG:
    STATIC_URL = f'/static/{SITE_NAME}/'
    STATIC_ROOT = BASE_DIR / 'public' / SITE_NAME

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'electeez'),
        'PASSWORD': os.getenv('DB_PASS', None),
        'HOST': os.getenv('DB_HOST', None),
        'USER': os.getenv('DB_USER', None),
        'PORT': os.getenv('DB_PORT', None),
    }
}

