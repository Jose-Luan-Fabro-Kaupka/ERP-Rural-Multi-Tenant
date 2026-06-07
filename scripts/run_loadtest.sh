#!/usr/bin/env bash
# Teste de carga com Locust para validar desempenho multi-tenant e pressionar o HPA no cluster.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export LOCUST_USERNAME="${LOCUST_USERNAME:-}"
export LOCUST_PASSWORD="${LOCUST_PASSWORD:-}"
HOST="${LOCUST_HOST:-http://tenant1.localhost:8000}"
exec locust -f locustfile.py --host="$HOST" "$@"
