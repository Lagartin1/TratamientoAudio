FROM python:3.11-slim

# Evita buffers en salida para logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala compiladores mínimos si hacen falta (psycopg2-binary suele evitar compilación, pero mantenemos herramientas ligeras).
# Usamos modo no-interactivo para evitar prompts de debconf y añadimos netcat para el entrypoint.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
       build-essential gcc libpq-dev netcat-openbsd ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && unset DEBIAN_FRONTEND

# Copia requerimientos e instala. Añadimos gunicorn para producción.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiamos el resto del código
COPY . .

# Puerto usado por la app (configurable con APP_PORT)
EXPOSE 5000

# Arranca con gunicorn apuntando al objeto `app` definido en main.py
# Copiamos y exponemos el entrypoint que esperará la DB y creará tablas
COPY docker_entrypoint.py ./docker_entrypoint.py
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# ENTRYPOINT ejecuta el script de preparación y luego arranca gunicorn
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
