"""
WSGI config for beampage project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use Heroku settings in production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 
                     'beampage.settings_heroku' if 'DYNO' in os.environ 
                     else 'beampage.settings')

application = get_wsgi_application()
