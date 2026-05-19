# Data Processor

Consumidor basico de cola Redis para procesar mensajes de audio.

## Requisitos

Antes de instalar las dependencias Python, necesitas tener `ffmpeg` disponible en el sistema.

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

## Uso

```bash
cd data-processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python consumer.py
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

Cuando llegue el mensaje, el consumidor deberia imprimir:

```bash
[consumer] message received from 'audio_tasks': {'audio_id': '123', 'file_path': '/tmp/audio.wav'}
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

Ejecutar tests:

```bash
pytest
```

El test de Redis se omite automaticamente si no hay un servidor Redis disponible en `REDIS_URL`.

Variables disponibles:

- `REDIS_URL`: URL de conexion a Redis.
- `REDIS_QUEUE_NAME`: nombre de la lista usada como cola.
- `REDIS_BLOCK_TIMEOUT_SECONDS`: timeout de espera en `BLPOP`.
- `LOG_LEVEL`: nivel de logs.
