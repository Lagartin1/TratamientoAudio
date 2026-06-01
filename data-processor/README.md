# Data Processor

Consumidor de cola Redis para procesar audios guardados en Postgres.

El flujo esperado es:

1. Un registro existe en la tabla `audios` con su `audio_file`.
2. Se agrega a Redis un mensaje con el `audio_id`.
3. El consumidor lee la cola, obtiene el audio desde Postgres, lo procesa y actualiza los campos calculados.
4. El consumidor registra eventos en `log_sample` y guarda aves detectadas en `birds`.

## Requisitos

- Python 3.11 o superior.
- Redis disponible en `REDIS_URL`.
- Postgres disponible en `SUPABASE_DB_URL`, `DATABASE_URL`, `POSTGRES_URL` o variables separadas de Supabase.
- `ffmpeg` instalado en el sistema.

En Ubuntu/Debian:

```bash
sudo apt update
sudo apt install ffmpeg
```

En macOS con Homebrew:

```bash
brew install ffmpeg
```

Puedes verificarlo con:

```bash
ffmpeg -version
```

## Instalacion

```bash
cd data-processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion

Crea `src/.env` usando `src/.env.example` como referencia.

Ejemplo local:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_NAME=audio_tasks
REDIS_BLOCK_TIMEOUT_SECONDS=5
LOG_LEVEL=INFO
SUPABASE_DB_URL=postgresql://admin:admin123@localhost:5432/mi_bd
POSTGRES_POOL_SIZE=5
POSTGRES_MAX_OVERFLOW=10
```

Ejemplo con Supabase Pooler:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_NAME=audio_tasks
REDIS_BLOCK_TIMEOUT_SECONDS=5
LOG_LEVEL=INFO
user=postgres.<project-ref>
password=<password>
host=aws-1-us-east-2.pooler.supabase.com
port=5432
dbname=postgres
POSTGRES_SSLMODE=require
```

Variables disponibles:

- `REDIS_URL`: URL de conexion a Redis.
- `REDIS_QUEUE_NAME`: nombre de la lista usada como cola.
- `REDIS_BLOCK_TIMEOUT_SECONDS`: timeout de espera en `BLPOP`.
- `LOG_LEVEL`: nivel de logs.
- `SUPABASE_DB_URL`, `DATABASE_URL` o `POSTGRES_URL`: URL de conexion a Postgres.
- `user`, `password`, `host`, `port`, `dbname`: alternativa para configurar la conexion con los valores separados que entrega Supabase.
- `POSTGRES_SSLMODE`: modo SSL usado cuando se construye la URL desde variables separadas. Por defecto: `require`.
- `POSTGRES_POOL_SIZE`: tamano del pool de conexiones. No se usa con Supabase Pooler.
- `POSTGRES_MAX_OVERFLOW`: conexiones extra permitidas sobre el pool. No se usa con Supabase Pooler.

## Ejecutar consumidor

Desde `data-processor`:

```bash
export PYTHONPATH=src
python src/consumer.py
```

Si se lanza correctamente, deberias ver una salida parecida a:

```bash
[consumer] starting consumer.py
[consumer] connecting to Redis: redis://localhost:6379/0
[consumer] consumer launched and listening on queue: audio_tasks
```

Enviar un mensaje de prueba:

```bash
redis-cli LPUSH audio_tasks '{"audio_id":"123","file_path":"/tmp/audio.wav"}'
```

El consumidor usa `audio_id` para buscar el archivo binario en Postgres. El campo `file_path` no es requerido por el flujo actual.

Cuando llegue el mensaje, el consumidor deberia imprimir:

```bash
[consumer] processing message: {'audio_id': '123', 'file_path': '/tmp/audio.wav'}
```

Otra forma de saber si el proceso esta corriendo:

```bash
ps aux | grep consumer.py
```

Y para revisar si la cola tiene mensajes pendientes:

```bash
redis-cli LLEN audio_tasks
```

Si `LLEN` devuelve `0` despues de enviar el mensaje, significa que el consumidor lo tomo desde Redis.

## Ejecutar con Docker

Construir y lanzar el contenedor:

```bash
cd data-processor
./run-data-processor.sh
```

El script usa por defecto:

- Imagen: `data-processor:local`.
- Contenedor: `data-processor`.
- Variables: `src/.env`.
- Red: `host`.

La red `host` permite que `REDIS_URL=redis://localhost:6379/0` apunte al Redis que corre en tu maquina.

Tambien puedes sobrescribir esos valores:

```bash
IMAGE_NAME=data-processor:dev \
CONTAINER_NAME=data-processor \
ENV_FILE=src/.env \
NETWORK_MODE=host \
./run-data-processor.sh
```

Para usar una red Docker existente, revisa primero el nombre:

```bash
docker network ls
```

Luego lanza el contenedor indicando esa red:

```bash
NETWORK_MODE=mi-red-docker ./run-data-processor.sh
```

Si Redis tambien corre dentro de esa red Docker, en `src/.env` usa el nombre del contenedor Redis en vez de `localhost`. Por ejemplo, si el contenedor se llama `redis`:

```env
REDIS_URL=redis://redis:6379/0
```

Ver logs del contenedor:

```bash
docker logs -f data-processor
```

## Tests

Ejecutar toda la suite:

```bash
pytest
```

Ejecutar solo los tests del consumidor:

```bash
pytest test/test_consumer.py
```

Si aparece un error de modulo, por ejemplo `ModuleNotFoundError: No module named 'consumer'`, ejecuta el test agregando `src` al `PYTHONPATH`:

```bash
export PYTHONPATH=src
pytest test/test_consumer.py
```

El test de Redis se omite automaticamente si no hay un servidor Redis disponible en `REDIS_URL`.

El test end-to-end con `queltehue.wav` se omite automaticamente si no hay conexion a Postgres. Para probarlo contra la BD local:

```bash
SUPABASE_DB_URL=postgresql://admin:admin123@localhost:5432/mi_bd pytest test/test_consumer.py
```

### Tests con Docker

Los tests de Docker leen variables desde `test/.env`. Puedes crearlo desde `test/.env.example`.

Variables usadas:

```env
RUN_DOCKER_TESTS=1
CONTAINER_NAME=data-processor
DOCKER_ENV_FILE=src/.env
DOCKER_NETWORK_MODE=host
DOCKER_E2E_TIMEOUT_SECONDS=240
```

Para ejecutar los tests Docker:

```bash
cd data-processor
pytest test/test_docker.py -q -rs
```

Estos tests validan:

- Que la imagen Docker se construye correctamente.
- Que el contenedor puede importar `consumer` y tiene `ffmpeg`.
- Que el contenedor corriendo puede conectarse a Redis.
- Que el contenedor corriendo consume un mensaje real, procesa `test/queltehue.wav` y actualiza Postgres.

Para el test end-to-end de Docker, antes debes tener Redis y el contenedor `data-processor` corriendo:

```bash
docker start redis
./run-data-processor.sh
pytest test/test_docker.py -q -rs
```

Si el contenedor no esta corriendo, los tests que dependen de el se omiten automaticamente.
