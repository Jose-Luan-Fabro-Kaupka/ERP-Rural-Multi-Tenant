#!/usr/bin/env bash
# Executa 3 cenários Locust (10, 50, 100 usuários) DENTRO do cluster Kubernetes,
# eliminando o gargalo do kubectl port-forward.
#
# Como funciona:
#   1. Cria (se necessário) o ConfigMap `locust-scripts` e o Pod `locust-runner`.
#   2. Para cada cenário, executa `kubectl exec` disparando o locust dentro do pod.
#   3. Monitora `kubectl top pods` e HPA em paralelo (host).
#   4. Copia os CSVs de saída do pod para docs/locust_runs/.
#
# Pré-requisitos:
#   - Cluster Kubernetes com django-api Service em agro-saas.
#   - Tenant `loadtest` com domínio `loadtest.localhost` e usuário `locust/locust123`.
set -euo pipefail

DURATION="${1:-2m}"
NAMESPACE="${NAMESPACE:-agro-saas}"
POD="${POD:-locust-runner}"
OUT_DIR="${OUT_DIR:-docs/locust_runs}"
MON_INTERVAL="${MON_INTERVAL:-5}"

mkdir -p "$OUT_DIR"

echo "== Aplicando manifests do runner =="
kubectl apply -f scripts/locust-in-cluster.yaml

echo "== Aguardando pod locust-runner ficar Ready =="
kubectl wait --for=condition=Ready -n "$NAMESPACE" pod/"$POD" --timeout=120s

run_scenario() {
    local users="$1"; local rate="$2"; local label="$3"
    local csv_prefix_in_pod="/output/locust_${label}"
    local csv_local_prefix="$OUT_DIR/locust_${label}"
    local mon_csv="$OUT_DIR/monitor_${label}.csv"
    local log_file="$OUT_DIR/locust_${label}.log"

    echo "=========================================="
    echo "  Cenário: ${users} usuários (rate ${rate}/s, duração ${DURATION})"
    echo "=========================================="

    echo "-- HPA antes --" | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get hpa django-api-hpa -n "$NAMESPACE" 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get deploy django-api -n "$NAMESPACE" 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"

    # Monitor em background (kubectl top + HPA)
    ./scripts/monitor_k8s.sh "$mon_csv" "$MON_INTERVAL" &
    local mon_pid=$!

    # Executa locust dentro do pod. `-i` mantém stdin aberto p/ evitar tty issues.
    kubectl exec -n "$NAMESPACE" "$POD" -- \
        locust \
            -f /opt/locust/locustfile.py \
            --host "http://django-api.agro-saas.svc.cluster.local" \
            --headless \
            -u "$users" -r "$rate" -t "$DURATION" \
            --csv "$csv_prefix_in_pod" \
            --only-summary 2>&1 | tee "$log_file" | tail -n 40

    # Encerra monitor
    kill -9 "$mon_pid" 2>/dev/null || true
    pkill -9 -f "monitor_k8s.sh $mon_csv" 2>/dev/null || true

    # Copia CSVs do pod para local
    for suffix in stats stats_history failures exceptions; do
        kubectl cp -n "$NAMESPACE" "$POD:${csv_prefix_in_pod}_${suffix}.csv" \
            "${csv_local_prefix}_${suffix}.csv" 2>/dev/null || echo "aviso: sem ${suffix}.csv"
    done

    echo "-- HPA depois --" | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get hpa django-api-hpa -n "$NAMESPACE" 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    kubectl get deploy django-api -n "$NAMESPACE" 2>&1 | tee -a "$OUT_DIR/hpa_snapshots.log"
    echo | tee -a "$OUT_DIR/hpa_snapshots.log"

    echo "-- cool-down 30s --"
    sleep 30
}

: > "$OUT_DIR/hpa_snapshots.log"

{
    echo "== Baseline (sem carga) =="
    kubectl top pods -n "$NAMESPACE"
    kubectl get hpa django-api-hpa -n "$NAMESPACE"
} | tee "$OUT_DIR/baseline.log"

run_scenario 10  2  "10"
run_scenario 50  5  "50"
run_scenario 100 10 "100"

echo "== Estado final =="
kubectl top pods -n "$NAMESPACE" | tee -a "$OUT_DIR/baseline.log"
kubectl get hpa django-api-hpa -n "$NAMESPACE" | tee -a "$OUT_DIR/baseline.log"
kubectl describe hpa django-api-hpa -n "$NAMESPACE" 2>&1 | tee "$OUT_DIR/hpa_describe.log"
