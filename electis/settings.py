from django.utils.translation import gettext_lazy as _

from electeez_common.settings import *

SITE_ID = 1
SITE_NAME = 'baloti_djelectionguard'
# SITE_NAME = 'electis'

INSTALLED_APPS += ['electis']

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', ('English')),
    ('de', ('German')),
    ('fr', ('French')),
    ('es', ('Spanish')),
    ('zh-cn', ('Chinese')),
    ('uk', ('Ukrainian')),
    ('ja', ('Japanese')),
    ('ru', ('Russian')),
    ('id', ('Indonesian')),

)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'public'
STATICFILES_DIRS = [
    BASE_DIR / 'electis' / 'static',
    BASE_DIR / 'static',
    BASE_DIR / 'baloti_djelectionguard' / 'static',
]

STATIC_HOME_PAGE = 'landing/index.html'

if DEBUG:
    STATIC_URL = f'/static/{SITE_NAME}/'
    STATIC_ROOT = BASE_DIR / 'public' / SITE_NAME

SASS_PROCESSOR_ROOT = STATIC_ROOT

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

TEMPLATE_CONTEXT_PROCESSORS = ['django.core.context_processors.request',]

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@electis.app')
