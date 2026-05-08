#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

# ── Fix encoding Windows ──────────────────────────────────────────────────────
# Evita UnicodeDecodeError en psycopg2 cuando el nombre del usuario o equipo
# Windows contiene caracteres con acento (Jose, Maria, etc.)
# DEBE ir antes de cualquier import de Django o psycopg2.
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONUTF8', '1')
for _pg in ('PGUSER', 'PGPASSWORD', 'PGHOST', 'PGDATABASE', 'PGPORT',
            'PGPASSFILE', 'PGSSLCERT', 'PGSSLKEY', 'PGREQUIRESSSL'):
    os.environ.pop(_pg, None)
# ─────────────────────────────────────────────────────────────────────────────


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resp_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
