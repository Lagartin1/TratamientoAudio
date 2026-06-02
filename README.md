# TratamientoAudio

Sistema distribuido para recolección, procesamiento y visualización de audios ambientales con detección de aves mediante BirdNET.

## Arquitectura

| Componente           | Descripción                                      | Puerto |
|----------------------|--------------------------------------------------|--------|
| `root-backend`       | API principal (autenticación, consultas públicas)| 4001   |
| `collector-api`      | API para recepción de audios desde dispositivos  | 4000   |
| `collector-frontend` | UI para dispositivos colectores                  | 4200   |
| `public-frontend`    | UI pública con mapa de calor de detecciones      | 4201   |
| `data-processor`     | Worker que procesa audios y detecta aves         | 5000   |

## Requisitos previos

- Docker y Docker Compose (Recomendado para el despliegue completo)
- Python 3.11+ (Para desarrollo manual)
- Node.js 20+ y npm 10+ (Para desarrollo manual de UI)
- Redis y PostgreSQL (Si no se usa Docker)
- ffmpeg (Solo para `data-processor` sin Docker)

---

## Quick Start con Docker Compose (Recomendado)

La forma más rápida para levantar todo el sistema:

```bash
# Desde la raíz del proyecto
docker compose up --build -d
```

Esto levantará automáticamente:

* **PostgreSQL** (puerto 5432) — base de datos principal
* **Redis** (puerto 6379) — cola de tareas
* **root-backend** (puerto 4001) — API principal
* **collector-api** (puerto 4000) — API de recepción de audios
* **data-processor** (puerto 5000) — worker para procesar audios
* **collector-frontend** (puerto 4200) — UI para colectores
* **public-frontend** (puerto 4201) — UI pública

### Verificar que todo está corriendo

```bash
# Ver estado de todos los servicios
docker compose ps

# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f root-backend
```

### Configuración inicial

Para que el sistema funcione correctamente, es necesario crear un usuario genérico en la base de datos. Accede a la base de datos PostgreSQL y ejecuta:

```sql
-- Crear usuario genérico si no existe
INSERT INTO users (email, name, role, created_at)
VALUES ('generic@example.com', 'Usuario Genérico', 'user', NOW())
ON CONFLICT DO NOTHING;
```

Alternativamente, puedes usar el endpoint de la API para crear el usuario:

```bash
curl -X POST http://localhost:4001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"generic@example.com","name":"Usuario Genérico","password":"changeme"}'
```

### Acceder a los servicios

Todos los servicios están disponibles a través de nginx en el puerto 80 (o el puerto configurado en `NGINX_HTTP_PORT`):

| Servicio | URL |
| --- | --- |
| public-frontend | http://localhost/ |
| collector-frontend | http://localhost/collector/ |
| root-backend API | http://localhost/api/ |
| collector-api | http://localhost/collector-api/ |

También puedes acceder directamente a los servicios en sus puertos internos:

| Servicio | Puerto |
| --- | --- |
| PostgreSQL | 5432 |
| Redis | 6379 |

### Detener todo

```bash
docker compose down

# Detener y eliminar volúmenes (base de datos)
docker compose down -v
```

---

## Despliegue Manual (Servicio por Servicio)

Si prefieres levantar los servicios individualmente para desarrollo, sigue estos pasos:

### 0. Levantar Redis

Requerido por `data-processor`. Levántalo una sola vez como contenedor:

```bash
docker run -d --name redis -p 6379:6379 --restart unless-stopped redis:7-alpine
```

Verificar:

```bash
docker exec -it redis redis-cli ping     # debe responder: PONG
```

Si el contenedor ya existe y está detenido: `docker start redis`.

---

### 1. root-backend

Backend principal con Docker.

```bash
cd root-backend
cp .env.example .env
# Editar .env con las credenciales de Supabase y JWT
docker compose up --build -d
```

Verificar que levantó:

```bash
curl http://localhost:4001/
```

**Variables de entorno (`root-backend/.env`)**

```env
FLASK_ENV=development
APP_HOST=0.0.0.0
APP_PORT=4001
SECRET_KEY=change-me

DB_HOST=aws-0-region.pooler.supabase.com
DB_PORT=6543
DB_USER=postgres.project-ref
DB_PASSWORD=your-password
DB_NAME=postgres

SUPABASE_URL=https://project-ref.supabase.co
SUPABASE_KEY=your-anon-key

JWT_SECRET_KEY=change-me-jwt
JWT_EXPIRATION_HOURS=24

AUTH_REQUIRED=false
CORS_ORIGINS=http://localhost:4201,http://localhost:4200
```

---

### 2. collector-api

API de recepción de audios. Puede correr con pip o con conda.

**Con pip**

```bash
cd collector-api
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env
python main.py
```

**Con conda**

```bash
cd collector-api
conda env create -f environment.yml
conda activate tratamiento-audio-backend
cp .env.example .env
python main.py
```

La API queda disponible en `http://localhost:4000`.

**Inicializar base de datos (solo primera vez)**
Si las tablas aún no existen, ejecutar el script SQL:

```bash
# Con psql
psql -h <host> -U <user> -d postgres -f sql/init_schema.sql
```

O desde Python:

```python
from webiste.app.extensions import db
from bootstrap import create_app
app = create_app()
with app.app_context():
    db.create_all()
```

**Variables de entorno (`collector-api/.env`)**

```env
FLASK_ENV=development
APP_HOST=0.0.0.0
APP_PORT=4000
SECRET_KEY=change-me

DATABASE_URL=sqlite:///database.db   # o URL de Supabase

SUPABASE_URL=
SUPABASE_KEY=

AUTH_REQUIRED=false
CORS_ORIGINS=*
```

---

### 3. data-processor

Worker que consume la cola Redis, obtiene el audio desde Postgres, lo analiza con BirdNET y guarda los resultados.

**Con Docker (recomendado para dev manual)**

```bash
cd data-processor
cp src/.env.example src/.env
# Editar src/.env con REDIS_URL y credenciales de Postgres
./run-data-processor.sh
```

Ver logs:

```bash
docker logs -f data-processor
```

**Sin Docker**
Requiere `ffmpeg` instalado:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

```bash
cd data-processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp src/.env.example src/.env
# Editar src/.env
export PYTHONPATH=src
python src/consumer.py
```

**Variables de entorno (`data-processor/src/.env`)**

```env
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_NAME=audio_tasks
REDIS_BLOCK_TIMEOUT_SECONDS=5
LOG_LEVEL=INFO

# Opción A: URL completa
SUPABASE_DB_URL=postgresql://user:password@host:5432/postgres

# Opción B: variables separadas (Supabase Pooler)
user=postgres.<project-ref>
password=<password>
host=aws-0-region.pooler.supabase.com
port=5432
dbname=postgres
POSTGRES_SSLMODE=require
```

---

### 4. collector-frontend

UI Angular para dispositivos colectores.

```bash
cd collector-frontend
npm install
cp .env.example .env
# Editar .env con la URL del collector-api
npm start
```

Disponible en `http://localhost:4200`.

**Variables de entorno (`collector-frontend/.env`)**

```env
NG_APP_URL_COLLECTOR_API=http://localhost:4000
```

---

### 5. public-frontend

UI pública con mapa de calor de detecciones de aves.

```bash
cd public-frontend
npm install
# Configurar variables de entorno si aplica
npm start
```

Disponible en `http://localhost:4201`.

---

## Orden de arranque recomendado (Manual)

Si no utilizas el Docker Compose principal, este es el orden seguro para levantar los servicios:

1. **PostgreSQL / Supabase** — debe estar disponible antes que cualquier API.
2. **Redis** — requerido por `collector-api` y `data-processor`.
3. **root-backend** — `docker compose up -d`
4. **collector-api** — `python main.py`
5. **data-processor** — `./run-data-processor.sh` o `python src/consumer.py`
6. **collector-frontend** — `npm start`
7. **public-frontend** — `npm start`

---

## Tests

Cada componente tiene su propia suite de tests:

```bash
# Backends Python
cd collector-api && pytest
cd root-backend  && pytest

# Data processor
cd data-processor
pytest
# Solo tests del consumidor
pytest test/test_consumer.py
# Con PYTHONPATH si hay errores de módulo
export PYTHONPATH=src && pytest test/test_consumer.py
```
