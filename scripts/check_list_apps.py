import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.test import RequestFactory

adapter = DefaultSocialAccountAdapter()
req = RequestFactory().get('/')
apps = adapter.list_apps(req, provider='google')
print('list_apps length:', len(apps))
for a in apps:
    print('app:', getattr(a, 'provider', None), getattr(a, 'name', None), getattr(a, 'client_id', None), getattr(a, 'settings', {}))
app = adapter.get_app(req, provider='google')
print('\nget_app selected:', getattr(app, 'provider', None), getattr(app, 'name', None), getattr(app, 'client_id', None), getattr(app, 'settings', {}))
