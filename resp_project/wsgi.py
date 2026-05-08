# -*- coding: utf-8 -*-
import os
import sys

# Fix encoding Windows (mismo que manage.py)
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')
for _pg in ('PGUSER', 'PGPASSWORD', 'PGHOST', 'PGDATABASE', 'PGPORT',
            'PGPASSFILE', 'PGSSLCERT', 'PGSSLKEY', 'PGREQUIRESSSL'):
    os.environ.pop(_pg, None)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resp_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
