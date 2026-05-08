@echo off
:: Fuerza UTF-8 en el proceso Python para evitar errores de encoding con psycopg2
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PGUSER=
set PGPASSWORD=
set PGHOST=
set PGDATABASE=
set PGPORT=
python manage.py runserver %*
