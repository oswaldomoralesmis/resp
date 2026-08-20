#!/usr/bin/env bash
# Instala/actualiza el RESP en este servidor AlmaLinux: crea el usuario de
# sistema, el entorno virtual, el .env, corre migraciones y collectstatic,
# instala el servicio systemd de Gunicorn y el vhost de nginx, y ajusta
# SELinux/firewalld. Asume que Python, PostgreSQL, nginx y systemd YA están
# instalados, y que el código del proyecto YA fue copiado a PROJECT_DIR
# (git clone / rsync / scp) — este script no descarga el código.
#
# Idempotente: se puede volver a correr para actualizar el código (después
# de un nuevo git pull) sin duplicar usuarios, .env ni la base de datos.
#
# Uso típico:
#   sudo DB_PASSWORD='la-misma-que-usó-en-crear_bd.sh' \
#        ALLOWED_HOSTS='10.20.30.40' \
#        ./deploy/instalar.sh
set -euo pipefail

# ── Configuración (todas sobreescribibles por variable de entorno) ────────
PROJECT_DIR="${PROJECT_DIR:-/opt/resp_project}"
APP_USER="${APP_USER:-resp}"
NGINX_GROUP="${NGINX_GROUP:-nginx}"
DB_NAME="${DB_NAME:-resp_db}"
DB_USER="${DB_USER:-resp_user}"
DB_PORT="${DB_PORT:-5440}"
ALLOWED_HOSTS="${ALLOWED_HOSTS:-}"
NGINX_PORT="${NGINX_PORT:-9000}"

log() { echo -e "\n==> $*"; }

# ── Chequeos previos ────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: ejecute este script con sudo/root." >&2
    exit 1
fi

if [[ ! -f "${PROJECT_DIR}/manage.py" ]]; then
    echo "ERROR: no se encontró ${PROJECT_DIR}/manage.py." >&2
    echo "  Copie primero el código del proyecto a ${PROJECT_DIR} (git clone/rsync/scp)." >&2
    exit 1
fi

if [[ ! -f "${PROJECT_DIR}/.env" && -z "${DB_PASSWORD:-}" ]]; then
    echo "ERROR: no existe ${PROJECT_DIR}/.env y no definió DB_PASSWORD para crearlo." >&2
    echo "  Ejemplo: sudo DB_PASSWORD='clave-segura' ./deploy/instalar.sh" >&2
    exit 1
fi

# pg_config puede existir mas no estar en el PATH restringido de sudo
# (secure_path), sobre todo si PostgreSQL viene del repositorio PGDG
# (/usr/pgsql-XX/bin) en vez del paquete del sistema. Se busca ahí también
# antes de darlo por no encontrado.
if ! command -v pg_config >/dev/null 2>&1; then
    for d in /usr/pgsql-*/bin /usr/lib64/pgsql*/bin /usr/lib/postgresql/*/bin; do
        [[ -x "${d}/pg_config" ]] && export PATH="${d}:${PATH}" && break
    done
fi
if ! command -v pg_config >/dev/null 2>&1; then
    echo "AVISO: no se encontró pg_config en PATH ni en ubicaciones comunes de PostgreSQL."
    echo "  Si el 'pip install' de más abajo falla compilando psycopg2, instale:"
    echo "  dnf install postgresql-devel gcc python3-devel"
    echo "  (si ya corrió este script antes y el venv ya tiene psycopg2 instalado, esto no bloquea nada)."
fi
command -v gcc >/dev/null 2>&1 || echo "AVISO: no se encontró gcc; si psycopg2 no está ya instalado en el venv, el pip install de más abajo fallará al compilarlo."
for prog in nginx systemctl semanage; do
    command -v "$prog" >/dev/null 2>&1 || echo "AVISO: no se encontró '$prog' en PATH; algunos pasos podrían fallar."
done

if [[ -z "$ALLOWED_HOSTS" ]]; then
    ALLOWED_HOSTS="$(hostname -I 2>/dev/null | awk '{print $1}')"
    [[ -n "$ALLOWED_HOSTS" ]] || { echo "ERROR: no se pudo detectar la IP del servidor; defina ALLOWED_HOSTS." >&2; exit 1; }
    log "ALLOWED_HOSTS no definido, se detectó automáticamente: ${ALLOWED_HOSTS}"
fi

# ── Usuario/grupo de sistema para correr la app ────────────────────────────
if ! id "$APP_USER" >/dev/null 2>&1; then
    log "Creando usuario de sistema '${APP_USER}'..."
    useradd --system --no-create-home --shell /sbin/nologin "$APP_USER"
else
    log "Usuario '${APP_USER}' ya existe, se reutiliza."
fi

# ── Carpetas ────────────────────────────────────────────────────────────
log "Preparando carpetas de datos (media, staticfiles)..."
mkdir -p "${PROJECT_DIR}/media" "${PROJECT_DIR}/staticfiles"

# ── Entorno virtual y dependencias ─────────────────────────────────────
if [[ ! -x "${PROJECT_DIR}/venv/bin/python" ]]; then
    log "Creando entorno virtual..."
    python3 -m venv "${PROJECT_DIR}/venv"
fi
log "Instalando/actualizando dependencias (requirements.txt)..."
"${PROJECT_DIR}/venv/bin/pip" install --upgrade pip --quiet
"${PROJECT_DIR}/venv/bin/pip" install -r "${PROJECT_DIR}/requirements.txt" --quiet
"${PROJECT_DIR}/venv/bin/pip" install gunicorn --quiet

# ── .env ────────────────────────────────────────────────────────────────
if [[ ! -f "${PROJECT_DIR}/.env" ]]; then
    log "Generando ${PROJECT_DIR}/.env ..."
    SECRET_KEY="$("${PROJECT_DIR}/venv/bin/python" -c \
        'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    cat > "${PROJECT_DIR}/.env" <<EOF
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=${DB_PORT}

SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${ALLOWED_HOSTS}
EOF
    chmod 600 "${PROJECT_DIR}/.env"
else
    log "${PROJECT_DIR}/.env ya existe, no se modifica."
fi

# ── Plantillas Excel (no van en git, deben copiarse a mano) ────────────
for f in Catalogos_Sistema_RESP.xlsx Layout_Informacion_Basica.xlsx Layout_Bajas.xlsx \
         Layout_Datos_Personales.xlsx Catalogo_Fuente.xlsx Catalogo_Dependencia.xlsx \
         Catalogo_Categoria.xlsx Catalogo_Unidades_Admvas.xlsx Catalogo_Programas.xlsx \
         Catalogo_Proyectos.xlsx Catalogo_Plazas.xlsx; do
    if [[ ! -f "${PROJECT_DIR}/${f}" ]]; then
        echo "AVISO: falta ${PROJECT_DIR}/${f} (está en .gitignore, cópielo manualmente)."
    fi
done

# ── Dueño de todo el proyecto ────────────────────────────────────────────
chown -R "${APP_USER}:${APP_USER}" "$PROJECT_DIR"

# ── Migraciones, estáticos, catálogos, admin inicial ───────────────────
run_as_app() { runuser -u "$APP_USER" -- "${PROJECT_DIR}/venv/bin/python" "${PROJECT_DIR}/manage.py" "$@"; }

env_db_host="$(grep -E '^DB_HOST=' "${PROJECT_DIR}/.env" | tail -1 | cut -d= -f2-)"
env_db_port="$(grep -E '^DB_PORT=' "${PROJECT_DIR}/.env" | tail -1 | cut -d= -f2-)"
log "Verificando conexión a la base de datos (${env_db_host}:${env_db_port})..."
DBCHECK_LOG="$(mktemp)"
if run_as_app shell -c "from django.db import connection; connection.ensure_connection()" \
        > "$DBCHECK_LOG" 2>&1; then
    log "Conexión a la base de datos OK."
    rm -f "$DBCHECK_LOG"
else
    echo "ERROR: no se pudo conectar a PostgreSQL con los datos de ${PROJECT_DIR}/.env:" >&2
    tail -5 "$DBCHECK_LOG" >&2
    rm -f "$DBCHECK_LOG"
    echo "" >&2
    echo "  Causas típicas:" >&2
    echo "  - DB_HOST=${env_db_host} no es un host que pg_hba.conf acepte para este" >&2
    echo "    usuario/base. Si PostgreSQL corre en este mismo servidor, DB_HOST" >&2
    echo "    normalmente debe ser 'localhost' o '127.0.0.1', no la IP de red del" >&2
    echo "    servidor — edite ${PROJECT_DIR}/.env y vuelva a correr este script." >&2
    echo "  - O bien, agregue en pg_hba.conf una línea 'host ${DB_NAME} ${DB_USER} <host-real>/32 scram-sha-256'" >&2
    echo "    (o md5, según su configuración) y recargue PostgreSQL: sudo systemctl reload postgresql." >&2
    exit 1
fi

log "Aplicando migraciones..."
run_as_app migrate --noinput

log "Recolectando archivos estáticos..."
run_as_app collectstatic --noinput

if [[ -f "${PROJECT_DIR}/Catalogos_Sistema_RESP.xlsx" ]]; then
    log "Cargando catálogos base (solo agrega los que falten)..."
    runuser -u "$APP_USER" -- "${PROJECT_DIR}/venv/bin/python" "${PROJECT_DIR}/cargar_catalogos.py" || \
        echo "AVISO: cargar_catalogos.py terminó con error; revise el mensaje anterior."
else
    echo "AVISO: se omitió la carga de catálogos (falta Catalogos_Sistema_RESP.xlsx)."
fi

log "Verificando/creando el usuario administrador inicial..."
run_as_app setup_resp

# ── Permisos: nginx debe poder leer static/ y media/ ────────────────────
if getent group "$NGINX_GROUP" >/dev/null 2>&1; then
    log "Ajustando permisos de static/media para el grupo '${NGINX_GROUP}'..."
    chmod o+x "$PROJECT_DIR"
    for d in staticfiles media; do
        chgrp -R "$NGINX_GROUP" "${PROJECT_DIR}/${d}"
        find "${PROJECT_DIR}/${d}" -type d -exec chmod 750 {} \;
        find "${PROJECT_DIR}/${d}" -type f -exec chmod 640 {} \;
    done
else
    echo "AVISO: no existe el grupo '${NGINX_GROUP}'; nginx podría no poder leer static/media."
fi

# ── Servicio systemd (Gunicorn) ─────────────────────────────────────────
log "Instalando servicio systemd 'resp_project'..."
sed "s#/opt/resp_project#${PROJECT_DIR}#g; s/User=resp/User=${APP_USER}/; s/Group=resp/Group=${APP_USER}/" \
    "${PROJECT_DIR}/deploy/systemd/resp_project.service" > /etc/systemd/system/resp_project.service
systemctl daemon-reload
systemctl enable --now resp_project
systemctl restart resp_project

# ── nginx ─────────────────────────────────────────────────────────────
if command -v nginx >/dev/null 2>&1; then
    log "Instalando vhost de nginx..."
    sed "s#/opt/resp_project#${PROJECT_DIR}#g" \
        "${PROJECT_DIR}/deploy/nginx/resp_project.conf" > /etc/nginx/conf.d/resp_project.conf
    nginx -t
    systemctl enable --now nginx
    systemctl reload nginx
fi

# ── SELinux ──────────────────────────────────────────────────────────────
if command -v getenforce >/dev/null 2>&1 && [[ "$(getenforce)" == "Enforcing" ]]; then
    log "SELinux en modo Enforcing: ajustando políticas..."
    setsebool -P httpd_can_network_connect 1
    if command -v semanage >/dev/null 2>&1; then
        semanage fcontext -a -t httpd_sys_content_t "${PROJECT_DIR}/staticfiles(/.*)?" 2>/dev/null || true
        semanage fcontext -a -t httpd_sys_content_t "${PROJECT_DIR}/media(/.*)?" 2>/dev/null || true
        restorecon -Rv "${PROJECT_DIR}/staticfiles" "${PROJECT_DIR}/media" >/dev/null
        # SELinux solo deja a nginx escuchar en los puertos etiquetados
        # http_port_t (80, 443, 8080...); 9000 no es uno de ellos por
        # defecto, hay que agregarlo o nginx falla al arrancar.
        if ! semanage port -l 2>/dev/null | grep -qE "^http_port_t\s+tcp\s+.*(^|,)\s*${NGINX_PORT}(,|$)"; then
            semanage port -a -t http_port_t -p tcp "${NGINX_PORT}" 2>/dev/null || \
                semanage port -m -t http_port_t -p tcp "${NGINX_PORT}" 2>/dev/null || true
        fi
    else
        echo "AVISO: falta 'semanage' (paquete policycoreutils-python-utils); instálelo y vuelva a correr este script — si no, nginx no podrá leer static/media ni escuchar en el puerto ${NGINX_PORT}."
    fi
fi

# ── firewalld ────────────────────────────────────────────────────────────
if systemctl is-active --quiet firewalld 2>/dev/null; then
    log "Abriendo el puerto ${NGINX_PORT} en firewalld..."
    firewall-cmd --permanent --add-port="${NGINX_PORT}/tcp"
    firewall-cmd --reload
fi

log "Listo. Revise el estado con:"
echo "  systemctl status resp_project"
echo "  journalctl -u resp_project -f"
echo "  http://${ALLOWED_HOSTS}:${NGINX_PORT}/"
