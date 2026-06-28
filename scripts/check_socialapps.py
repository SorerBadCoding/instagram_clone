import os
import sys
import django
from django.db.models import Count

# Ensure project root is on sys.path so `config` settings import works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print('SITE_ID:', getattr(settings, 'SITE_ID', None))
print('\nSites:')
for s in Site.objects.all().values('id', 'domain', 'name'):
    print(s)

print('\nSocialApp provider counts:')
for row in SocialApp.objects.values('provider').annotate(count=Count('id')):
    print(row)

print('\nSocialApps for provider="google":')
for app in SocialApp.objects.filter(provider='google'):
    print('id:', app.id, 'name:', app.name, 'sites:', [s.id for s in app.sites.all()])
