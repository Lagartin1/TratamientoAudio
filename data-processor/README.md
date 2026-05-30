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
- Postgres disponible en `SUPABASE_DB_URL`, `DATABASE_URL` o `POSTGRES_URL`.
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

Variables disponibles:

- `REDIS_URL`: URL de conexion a Redis.
- `REDIS_QUEUE_NAME`: nombre de la lista usada como cola.
- `REDIS_BLOCK_TIMEOUT_SECONDS`: timeout de espera en `BLPOP`.
- `LOG_LEVEL`: nivel de logs.
- `SUPABASE_DB_URL`, `DATABASE_URL` o `POSTGRES_URL`: URL de conexion a Postgres.
- `POSTGRES_POOL_SIZE`: tamano del pool de conexiones.
- `POSTGRES_MAX_OVERFLOW`: conexiones extra permitidas sobre el pool.

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
