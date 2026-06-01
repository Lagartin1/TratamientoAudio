#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE_NAME="${IMAGE_NAME:-data-processor:local}"
CONTAINER_NAME="${CONTAINER_NAME:-data-processor}"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/src/.env}"
NETWORK_MODE="${NETWORK_MODE:-host}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker no esta instalado o no esta en el PATH" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "No existe el archivo de variables: $ENV_FILE" >&2
  echo "Crea uno desde: $SCRIPT_DIR/src/.env.example" >&2
  exit 1
fi

docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

docker run --rm -d -it \
  --name "$CONTAINER_NAME" \
  --env-file "$ENV_FILE" \
  --network "$NETWORK_MODE" \
  "$IMAGE_NAME"
