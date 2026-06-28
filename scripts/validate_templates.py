import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
from django.template import loader, TemplateSyntaxError
from django.test import RequestFactory

django.setup()

TEMPLATES_DIR = os.path.join(ROOT, 'templates')
errors = []
rf = RequestFactory()
req = rf.get('/')

for dirpath, dirnames, filenames in os.walk(TEMPLATES_DIR):
    for fn in filenames:
        if not fn.endswith('.html'):
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, TEMPLATES_DIR).replace('\\', '/')
        try:
            t = loader.get_template(rel)
            # attempt to render with a minimal context including request
            t.render({'request': req})
            print(f'OK: {rel}')
        except Exception as e:
            print(f'ERROR: {rel} -> {e.__class__.__name__}: {e}')
            errors.append((rel, e))

print('\nSummary:')
# Count templates
count = 0
for _, _, fs in os.walk(TEMPLATES_DIR):
    for f in fs:
        if f.endswith('.html'):
            count += 1
print(f'Templates checked: {count}')
print(f'Errors found: {len(errors)}')
if errors:
    for rel,e in errors:
        print(rel, repr(e))
