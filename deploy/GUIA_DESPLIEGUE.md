# Guía de despliegue — Servidor de pruebas (AlmaLinux)

Asume que el servidor **ya tiene instalados** Python 3, PostgreSQL (escuchando
en el puerto **5440**), nginx y systemd. Esta guía solo cubre: llevar el
código, crear la base de datos, y las configuraciones de carpetas,
Gunicorn y nginx. Acceso planeado: **por IP del servidor en el puerto
9000, sin dominio ni HTTPS** (servidor de pruebas) — `http://<IP>:9000/`.

Archivos de esta carpeta:

| Archivo | Para qué sirve |
|---|---|
| `crear_bd.sh` | Crea la base de datos y el rol en el PostgreSQL del puerto 5440 |
| `instalar.sh` | Deja todo listo: venv, `.env`, migraciones, estáticos, systemd, nginx, SELinux, firewalld |
| `gunicorn.conf.py` | Configuración de Gunicorn (la usa `instalar.sh`, no se toca a mano) |
| `systemd/resp_project.service` | Unidad systemd del proceso Gunicorn (la instala `instalar.sh`) |
| `nginx/resp_project.conf` | Vhost de nginx (lo instala `instalar.sh`) |
| `env.produccion.example` | Referencia de qué queda escrito en `/opt/resp_project/.env` |

---

## 0. Antes de empezar (en su máquina Windows)

Este repositorio tiene **cambios sin confirmar** (`git status`) de toda una
sesión de trabajo reciente — incluyendo dos migraciones nuevas que
**todavía no están en git**:

- `cargas/migrations/0011_alter_accesoexcepcioncarga_dependencia.py`
- `servidores/migrations/0013_alter_servidorpublico_sexo.py`

Si despliega el código tal cual está en el remoto sin subir esto primero,
el servidor de pruebas quedará con funcionalidad y esquema de BD
desactualizados. Haga commit (y push, si usa un remoto) de todo lo
pendiente antes de clonar en el servidor.

Además, estos archivos están en `.gitignore` (no viajan con `git clone`) y
la aplicación los necesita en la raíz del proyecto:

- `Catalogos_Sistema_RESP.xlsx` — catálogos iniciales (`cargar_catalogos.py`)
- `Layout_Informacion_Basica.xlsx`, `Layout_Bajas.xlsx`, `Layout_Datos_Personales.xlsx`
  — plantillas descargables desde "Cargar Layout"
- `Catalogo_Fuente.xlsx`, `Catalogo_Dependencia.xlsx`, `Catalogo_Categoria.xlsx`,
  `Catalogo_Unidades_Admvas.xlsx`, `Catalogo_Programas.xlsx`, `Catalogo_Proyectos.xlsx`,
  `Catalogo_Plazas.xlsx` — plantillas descargables desde cada catálogo (botón "⇓ Excel")

Cópielos al servidor por separado (`scp`) — el paso 3 de abajo se lo recuerda
si faltan.

---

## 1. Llevar el código al servidor

Con git remoto (recomendado):
```bash
sudo mkdir -p /opt/resp_project
sudo chown "$(whoami)" /opt/resp_project
git clone <url-de-su-repo> /opt/resp_project
```

Sin git remoto, desde Windows con `scp` (excluyendo `venv/`, que es de
Windows y no sirve en Linux):
```powershell
# PowerShell, ejecutar en la raíz del proyecto
scp -r cargas catalogos reportes servidores usuarios resp_project templates static deploy `
    manage.py requirements.txt .env.example README.md `
    usuario@servidor:/opt/resp_project/
```

## 2. Crear la base de datos (puerto 5440)

En el servidor:
```bash
cd /opt/resp_project
chmod +x deploy/*.sh
sudo DB_PASSWORD='defina-una-contraseña-segura-aquí' ./deploy/crear_bd.sh
```
Use variables `DB_NAME` / `DB_USER` si no quiere los valores por defecto
(`resp_db` / `resp_user`). El script es idempotente: si el rol/BD ya
existen, solo actualiza la contraseña.

## 3. Copiar los archivos Excel que no van en git

```bash
scp Catalogos_Sistema_RESP.xlsx Layout_*.xlsx Catalogo_*.xlsx usuario@servidor:/opt/resp_project/
```
Si los omite, `instalar.sh` avisa y sigue sin cargar catálogos — puede
correrlo de nuevo después.

## 4. Instalar (venv, `.env`, migraciones, systemd, nginx, SELinux, firewalld)

```bash
cd /opt/resp_project
sudo DB_PASSWORD='la-misma-contraseña-del-paso-2' \
     ALLOWED_HOSTS='<IP-del-servidor>' \
     ./deploy/instalar.sh
```
(Si omite `ALLOWED_HOSTS`, el script detecta la IP principal del servidor
solo.)

`instalar.sh` es idempotente: correrlo de nuevo (p.ej. tras un `git pull`
con código nuevo) reinstala dependencias, vuelve a migrar, recolecta
estáticos y reinicia el servicio, sin tocar el `.env` ni la base de datos
ya existentes.

Al final imprime la contraseña generada del usuario **admin** (comando
`setup_resp`) — cópiela, solo se muestra una vez (si ya existía un
administrador, el comando lo detecta y no crea uno nuevo).

## 5. Verificar

```bash
sudo systemctl status resp_project      # el proceso Gunicorn
sudo systemctl status nginx
sudo journalctl -u resp_project -f      # logs de Django/Gunicorn en vivo
curl -I http://localhost:9000/          # debe responder 200/302
```
Desde el navegador: `http://<IP-del-servidor>:9000/`

---

## Notas y decisiones de esta configuración

- **Gunicorn en loopback (`127.0.0.1:8001`)**, nunca expuesto directo:
  nginx es la única puerta de entrada, en el puerto **9000** (`NGINX_PORT`
  en `instalar.sh`, por si lo quiere cambiar otra vez). Evita además los
  problemas de permisos/SELinux de compartir un socket Unix entre el
  usuario de la app y `nginx`.
- **SELinux y el puerto 9000**: por defecto SELinux solo deja a `nginx`
  escuchar en los puertos ya etiquetados `http_port_t` (80, 443, 8080...);
  9000 no es uno de ellos, así que `instalar.sh` lo agrega con
  `semanage port -a -t http_port_t -p tcp 9000` cuando SELinux está en
  modo Enforcing.
- **Cargar/aceptar un layout grande no bloquea la respuesta HTTP**: subir o
  aceptar un archivo de layout corre la validación/aplicación real en un
  hilo aparte (`cargas/views.py`, `_lanzar_procesamiento`) — la página
  redirige de inmediato al detalle de la carga, que se auto-refresca cada 5
  segundos mientras `estado == 'procesando'`. Esto evita el 504 Gateway
  Timeout de nginx que daba antes con archivos grandes de Información
  Básica/Plazas. `gunicorn.conf.py` sube su `timeout` a 300s como margen
  extra, porque el worker `sync` sigue necesitando avisarle al *arbiter*
  de Gunicorn que sigue vivo mientras ese hilo trabaja.
- **Usuario de sistema dedicado `resp`** (sin shell, sin home) corre
  Gunicorn — no corre como root ni como el usuario de `nginx`.
- **`static/` y `media/` se sirven directo por nginx** (más rápido que
  pasarlos por Django); el resto del proyecto (código, `.env`, venv) no es
  legible por `nginx` — el script deja `staticfiles/` y `media/` con grupo
  `nginx` y el resto con dueño exclusivo `resp`.
- **`media/` contiene los Excel que suben las dependencias** (con
  RFC/CURP/percepciones). Al servirse por nginx sin autenticación
  adicional, cualquiera con la URL exacta del archivo podría descargarlo
  — es el mismo comportamiento que ya tiene la app hoy (`MEDIA_URL`
  público); si esto le preocupa para el ambiente de pruebas, es un cambio
  de arquitectura aparte (servir media a través de una vista con
  `@login_required`), fuera del alcance de este despliegue.
- **`DEBUG=False` y `ALLOWED_HOSTS` acotado** en el `.env` del servidor
  (antes `settings.py` los traía fijos en `True` / `['*']` sin poder
  cambiarlos; ahora `settings.py` los lee de `.env` si están definidos, y
  si no, se comporta exactamente igual que antes en su equipo Windows).
- **Sin HTTPS**: es un servidor de pruebas por IP. Si más adelante le
  asignan un dominio, se puede añadir `certbot --nginx` sin tocar nada de
  lo de aquí.
- **`psycopg2` (no `-binary`)** compila desde código fuente al hacer
  `pip install`; `instalar.sh` solo **avisa** (no bloquea) si no encuentra
  `pg_config`/`gcc` en el PATH de `sudo` — con `sudo`, el PATH suele venir
  recortado (`secure_path`) y no siempre incluye la carpeta `bin` de
  PostgreSQL aunque sí exista en el sistema.

## Actualizar el código más adelante

```bash
cd /opt/resp_project
sudo -u resp git pull            # o vuelva a copiar el código
sudo ./deploy/instalar.sh        # DB_PASSWORD ya no hace falta: .env ya existe
```

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| nginx responde 502 | Gunicorn no está corriendo | `systemctl status resp_project`, `journalctl -u resp_project -e` |
| nginx responde 504 al subir/aceptar un layout | Archivo tan grande que ni los 300s de margen alcanzan (poco común) | Revise `journalctl -u resp_project -f` mientras sube — si el hilo sigue corriendo, solo hace falta esperar y refrescar `carga_detalle`; si el worker murió, suba `timeout` en `deploy/gunicorn.conf.py` y reinicie (`systemctl restart resp_project`) |
| nginx da 403 en `/static/...` | Permisos/SELinux | Revise que `staticfiles/` sea grupo `nginx`; si SELinux está en Enforcing, corra de nuevo la sección SELinux de `instalar.sh` |
| `FATAL: no pg_hba.conf entry for host "<IP>"...` | `DB_HOST` en `.env` es la IP de red del servidor en vez de `localhost` — pg_hba.conf no tiene una regla para esa IP | Edite `/opt/resp_project/.env`, ponga `DB_HOST=localhost` (Postgres está en el mismo servidor), y vuelva a correr `instalar.sh`. Si de verdad necesita conectarse por esa IP, agregue una línea en `pg_hba.conf` (ver abajo) |
| Otro error de conexión a BD | Puerto/credenciales | Verifique `DB_PORT=5440` en `.env` y que `crear_bd.sh` corrió sin error |
| `pip install` falla compilando psycopg2 | Faltan `postgresql-devel`/`gcc` | `dnf install postgresql-devel gcc python3-devel` |
| Cambios de código no se ven | `collectstatic`/reinicio pendiente | Vuelva a correr `instalar.sh`, o `systemctl restart resp_project` |

### Si necesita agregar una regla a `pg_hba.conf`

Ubique el archivo (varía según cómo se instaló PostgreSQL, p.ej.
`/var/lib/pgsql/data/pg_hba.conf` o `/var/lib/pgsql/<versión>/data/pg_hba.conf`;
`sudo -u postgres psql -p 5440 -c 'SHOW hba_file;'` lo dice con certeza), agregue
una línea como:
```
host    resp_db    resp_user    127.0.0.1/32    scram-sha-256
```
(cambie `scram-sha-256` por `md5` si así están las demás líneas del archivo)
y recargue sin reiniciar conexiones activas:
```bash
sudo systemctl reload postgresql
```
