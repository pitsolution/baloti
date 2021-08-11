from django.utils.translation import gettext_lazy as _

from electeez_common.settings import *

SITE_ID = 2
SITE_NAME = 'neuilly'

INSTALLED_APPS += ['neuilly']

LANGUAGE_CODE = 'fr'

LANGUAGES = (
    ('fr', _('French')),
    ('en', _('English')),
)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'public'
STATICFILES_DIRS = [
    BASE_DIR / 'neuilly' / 'static',
    BASE_DIR / 'static',
]

if DEBUG:
    STATIC_URL = f'/static/{SITE_NAME}/'
    STATIC_ROOT = BASE_DIR / 'public' / SITE_NAME

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'neuilly'),
        'PASSWORD': os.getenv('DB_PASS', None),
        'HOST': os.getenv('DB_HOST', None),
        'USER': os.getenv('DB_USER', None),
        'PORT': os.getenv('DB_PORT', None),
    }
}

