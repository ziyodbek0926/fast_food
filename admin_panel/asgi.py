"""
ASGI config for admin_panel project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')

# Django ilovasining ASGI interfeysini yaratadi. Bu interfeys asinxron web serverlar bilan Django ilovasini bog'lash uchun ishlatiladi
application = get_asgi_application()
