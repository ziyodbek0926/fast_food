"""
WSGI config for admin_panel project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

# Django ilovasining WSGI interfeysini yaratadi. Bu interfeys web serverlar bilan Django ilovasini bog'lash uchun ishlatiladi
application = get_wsgi_application()
