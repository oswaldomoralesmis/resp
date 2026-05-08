@echo off
:: Fuerza UTF-8 en el proceso Python
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PGUSER=
set PGPASSWORD=
set PGHOST=
set PGDATABASE=
set PGPORT=

echo ================================================
echo  RESP - Setup en Windows
echo ================================================

echo.
echo [1/4] Instalando dependencias...
pip install -r requirements.txt

echo.
echo [2/4] Generando migraciones...
python manage.py makemigrations catalogos
python manage.py makemigrations usuarios
python manage.py makemigrations servidores
python manage.py makemigrations cargas
python manage.py makemigrations reportes

echo.
echo [3/4] Aplicando migraciones...
python manage.py migrate

echo.
echo [4/4] Creando usuario administrador...
python manage.py setup_resp

echo.
echo ================================================
echo  Listo. Ejecuta: runserver.bat
echo ================================================
pause
