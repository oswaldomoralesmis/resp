#!/usr/bin/env bash
# Crea la base de datos y el usuario del RESP en el PostgreSQL que ya está
# escuchando en el puerto 5440 de este servidor. Idempotente: se puede
# volver a correr sin duplicar nada (si el rol/BD ya existen, solo
# actualiza la contraseña del rol).
#
# Uso:
#   sudo DB_PASSWORD='una-contraseña-segura' ./crear_bd.sh
#
# Variables opcionales (si no se definen, usan estos valores por defecto,
# los mismos de .env.example):
#   DB_NAME=resp_db  DB_USER=resp_user  DB_PORT=5440
set -euo pipefail

DB_PORT="${DB_PORT:-5440}"
DB_NAME="${DB_NAME:-resp_db}"
DB_USER="${DB_USER:-resp_user}"

if [[ -z "${DB_PASSWORD:-}" ]]; then
    echo "ERROR: defina DB_PASSWORD antes de ejecutar este script." >&2
    echo "  Ejemplo: sudo DB_PASSWORD='clave-segura' ./crear_bd.sh" >&2
    exit 1
fi

echo "==> Verificando conexión a PostgreSQL en el puerto ${DB_PORT}..."
sudo -u postgres psql -p "$DB_PORT" -c '\conninfo' > /dev/null

echo "==> Creando/actualizando rol '${DB_USER}'..."
sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
      CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}';
   ELSE
      ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
   END IF;
END
\$\$;
SQL

echo "==> Creando base de datos '${DB_NAME}' (si no existe)..."
sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 \
        -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "==> Otorgando privilegios..."
sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 \
    -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
# PostgreSQL 15+ ya no da CREATE en el esquema public por defecto.
sudo -u postgres psql -p "$DB_PORT" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
    -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

echo "==> Listo. Base '${DB_NAME}' y usuario '${DB_USER}' preparados en el puerto ${DB_PORT}."
