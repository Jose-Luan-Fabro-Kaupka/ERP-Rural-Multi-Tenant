#!/usr/bin/env bash
# Roda 3 cenários de Locust (10, 50, 100 usuários) contra o cluster Kubernetes,
# monitorando kubectl top e HPA em paralelo.
#
# Pré-requisitos (feitos previamente):
#   1. kubectl port-forward svc/django-api 8080:80 -n agro-saas rodando
#   2. Tenant `loadtest` (domínio loadtest.localhost) criado no cluster
#   3. Usuário `locust` com senha `locust123` no tenant loadtest
#
# Uso: ./scripts/run_all_loadtests.sh [duracao] [host]
#   duracao default: 2m
#   host default: http://loadtest.localhost:8080
set -euo pipefail
DURATION="${1:-2m}"
HOST="${2:-http://127.0.0.1:8080}"
TENANT_HOST="${TENANT_HOST:-loadtest.localhost}"
OUT_DIR="${OUT_DIR:-docs/locust_runs}"
MON_INTERVAL="${MON_INTERVAL:-5}"
NAMESPACE="${NAMESPACE:-agro-saas}"

export LOCUST_USERNAME=locust
export LOCUST_PASSWORD=locust123
export LOCUST_TENANT_HOST="$TENANT_HOST"

mkdir -p "$OUT_DIR"

run_scenario() {
    local users="$1"; local rate="$2"; local label="$3"
    local csv_prefix="$OUT_DIR/locust_${label}"
    local mon_csv="$OUT_DIR/monitor_${label}.csv"

    echo "=========================================="
    echo "  Cenário: ${users} usuários (rate ${rate}/s, duração ${DURATION})"
    echo "=========================================="

    # Snapshot HPA antes
    echo "-- HPA antes --" | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get hpa django-api-hpa -n agro-saas 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get deploy django-api -n agro-saas 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"

    # Inicia monitor em background (setsid isola grupo p/ conseguir matar tudo)
    ./scripts/monitor_k8s.sh "$mon_csv" "$MON_INTERVAL" &
    local mon_pid=$!

    # Roda locust
    .venv/bin/locust -f locustfile.py \
        --host="$HOST" \
        --headless \
        -u "$users" -r "$rate" -t "$DURATION" \
        --csv "$csv_prefix" \
        --only-summary 2>&1 | tail -n 40

    # Encerra monitor sem depender do trap (SIGKILL para garantir)
    kill -9 "$mon_pid" 2>/dev/null || true
    pkill -9 -f "kubectl top pods -n $NAMESPACE" 2>/dev/null || true
    pkill -9 -f "monitor_k8s.sh $mon_csv" 2>/dev/null || true

    # Snapshot HPA depois
    echo "-- HPA depois --" | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get hpa django-api-hpa -n agro-saas 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get deploy django-api -n agro-saas 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    echo | tee -a "$OUT_DIR/hpa_snapshots.log"

    # Cool-down para estabilização entre cenários
    echo "-- cool-down 30s --"
    sleep 30
}

: > "$OUT_DIR/hpa_snapshots.log"

# Baseline
{
    echo "== Baseline (sem carga) =="
    kubectl top pods -n agro-saas
    kubectl get hpa django-api-hpa -n agro-saas
} | tee "$OUT_DIR/baseline.log"

run_scenario 10  2  "10"
run_scenario 50  5  "50"
run_scenario 100 10 "100"

echo "== Estado final =="
kubectl top pods -n agro-saas | tee -a "$OUT_DIR/baseline.log"
kubectl get hpa django-api-hpa -n agro-saas | tee -a "$OUT_DIR/baseline.log"
kubectl describe hpa django-api-hpa -n agro-saas 2>&1 | tee "$OUT_DIR/hpa_describe.log"
