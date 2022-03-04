"""
WSGI config for electeez project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

IPFS_PATH = os.getenv('IPFS_PATH', None)
if IPFS_PATH and not os.path.exists(IPFS_PATH):
    import subprocess
    out = subprocess.check_output(
        ['ipfs', 'init'],
        stderr=subprocess.PIPE,
        env=dict(IPFS_PATH=IPFS_PATH),
    )
    print(out.decode('utf8'))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electeez.settings')

application = get_wsgi_application()


