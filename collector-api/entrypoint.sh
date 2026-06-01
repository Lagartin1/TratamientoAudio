#!/usr/bin/env sh
# entrypoint.sh: espera a la base de datos, ejecuta creación de tablas si faltan y luego ejecuta el comando pasado
set -e

host_from_url() {
  # Extrae host:port de DATABASE_URL como postgres://user:pass@host:port/db
  echo "$1" | awk -F'[@:/]+' '{print $(NF-2)" "$(NF-1)}'
}

: ${DATABASE_URL:=}

if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL no está definida; continuando sin esperar DB."
else
  # Si la URL apunta a Supabase (host contiene 'supabase'), no intentamos conectar por nc
  HOSTNAME=$(echo "$DATABASE_URL" | sed -E 's#.*@([^:/]+):?.*#\1#')
  if echo "$HOSTNAME" | grep -qi "supabase"; then
    echo "DATABASE_URL parece apuntar a Supabase ($HOSTNAME). Omitiendo espera por TCP y creación local de tablas."
  else
  echo "Esperando a la base de datos definida en DATABASE_URL..."
  # Extraer host y puerto
  # Fallback a host 'db' si no se puede parsear
  HOST=$(echo "$DATABASE_URL" | sed -E 's#.*@([^:/]+):?([0-9]*).*#\1#')
  PORT=$(echo "$DATABASE_URL" | sed -E 's#.*@[^:/]+:([0-9]+).*#\1#')
  if [ -z "$HOST" ]; then
    HOST=db
  fi
  if [ -z "$PORT" ]; then
    PORT=5432
  fi

  echo "Comprobando $HOST:$PORT ..."
  # Espera a que el puerto esté accesible
  retry=0
  until nc -z "$HOST" "$PORT" >/dev/null 2>&1; do
    retry=$((retry+1))
    if [ $retry -gt 60 ]; then
      echo "Timeout esperando a la DB en $HOST:$PORT"
      exit 1
    fi
    echo "Esperando DB... intento $retry/60"
    sleep 1
  done
  echo "DB accesible en $HOST:$PORT"

  # Ejecutar script para crear tablas si faltan
  echo "Creando tablas si faltan..."
  python docker_entrypoint.py || echo "Creación de tablas terminó con código distinto de cero (continuando)"
  fi
fi

# Ejecutar comando por defecto
exec "$@"
