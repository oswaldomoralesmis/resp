# RESP — Registro Estatal de Servidores Públicos
## Gobierno del Estado de Tabasco

---

## Requisitos
- Python 3.10+
- PostgreSQL 14+
- pip packages (ver requirements.txt)

## Instalación

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL
```sql
CREATE DATABASE resp_db;
CREATE USER resp_user WITH PASSWORD 'resp_password';
GRANT ALL PRIVILEGES ON DATABASE resp_db TO resp_user;
ALTER DATABASE resp_db OWNER TO resp_user;
```

### 3. Variables de entorno (opcional)
Editar `resp_project/settings.py` con las credenciales reales de la base de datos.

### 4. Crear tablas
```bash
python manage.py makemigrations catalogos
python manage.py makemigrations usuarios
python manage.py makemigrations servidores
python manage.py makemigrations cargas
python manage.py makemigrations reportes
python manage.py migrate
```

### 5. Cargar catálogos desde Excel
Coloque el archivo `Catalogos_Sistema_RESP.xlsx` en la raíz del proyecto y ejecute:
```bash
python cargar_catalogos.py
```

### 6. Crear usuario administrador inicial
```bash
python manage.py setup_resp
```

### 7. Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

### 8. Iniciar servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Estructura de Módulos

| Módulo | Descripción |
|--------|-------------|
| `servidores` | Padrón de servidores, información básica quincenal, bajas |
| `catalogos` | 20+ catálogos del sistema (dependencias, categorías, municipios, etc.) |
| `usuarios` | Control de acceso con 7 roles: Plantilla, Validador, Empleado, Consulta, OIC, General, Administrador |
| `cargas` | Carga masiva de layouts (Básica, Datos Personales, Bajas) con validación |
| `reportes` | Padrón general, declaración patrimonial, entrega-recepción, bajas, compatibilidad, estadísticas |

## Roles de Usuario

| Rol | Permisos |
|-----|---------|
| **De Plantilla** | Sube layouts quincenales, captura individual |
| **Validador** | Valida estudios, cursos, idiomas, discapacidades |
| **Empleado** | Captura sus propios datos complementarios |
| **Consulta** | Genera todos los reportes |
| **OIC** | Consulta, padrón entrega-recepción, declaración patrimonial |
| **General** | Todas las opciones |
| **Administrador** | Todo + configuración, usuarios, catálogos |

## Tipos de Layouts

| Layout | Frecuencia | Campos principales |
|--------|-----------|-------------------|
| **Información Básica** | Quincenal | Institución, puesto, plaza, servidor, responsabilidades, inmueble |
| **Datos Personales** | Anual | Domicilio, tipo de sangre, correo personal |
| **Bajas** | Quincenal | Fecha baja, motivo, expediente |

---

## Colores Institucionales

| Color | Hex | Uso |
|-------|-----|-----|
| Azul institucional | `#1B4F72` | Sidebar, headers, botones primarios |
| Verde | `#1E8449` | Acciones positivas, botón cargar |
| Dorado | `#B7950B` | Acentos, nav activo |
| Rojo | `#C0392B` | Bajas, alertas de peligro |
