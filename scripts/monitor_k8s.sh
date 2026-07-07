#!/usr/bin/env bash
# Registra CPU/memória (kubectl top) e estado do HPA a cada N segundos em um CSV,
# até receber SIGTERM/SIGINT. Uso:
#   ./scripts/monitor_k8s.sh docs/locust_runs/monitor_100.csv 5
# Argumentos:
#   $1  arquivo de saída (obrigatório)
#   $2  intervalo em segundos (default 5)
set -euo pipefail
OUT="${1:?arquivo de saida obrigatorio}"
INTERVAL="${2:-5}"
NAMESPACE="${NAMESPACE:-agro-saas}"

mkdir -p "$(dirname "$OUT")"
echo "timestamp,pod,cpu_millicores,memory_mib,hpa_cpu_current,hpa_cpu_target,hpa_replicas,hpa_min,hpa_max" > "$OUT"

trap 'echo "monitor terminado"; exit 0' TERM INT

while true; do
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    hpa_line=$(kubectl get hpa django-api-hpa -n "$NAMESPACE" -o jsonpath='{.status.currentCPUUtilizationPercentage}|{.spec.targetCPUUtilizationPercentage}|{.status.currentReplicas}|{.spec.minReplicas}|{.spec.maxReplicas}' 2>/dev/null || echo "||||")
    hpa_cur_cpu="${hpa_line%%|*}"; rest="${hpa_line#*|}"
    hpa_tgt_cpu="${rest%%|*}"; rest="${rest#*|}"
    hpa_rep="${rest%%|*}"; rest="${rest#*|}"
    hpa_min="${rest%%|*}"; hpa_max="${rest#*|}"

    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read pod cpu mem _; do
        # cpu formato: 42m  (millicores); mem: 114Mi
        cpu_num="${cpu%m}"
        mem_num="${mem%Mi}"
        echo "$ts,$pod,$cpu_num,$mem_num,$hpa_cur_cpu,$hpa_tgt_cpu,$hpa_rep,$hpa_min,$hpa_max" >> "$OUT"
    done

    sleep "$INTERVAL"
done
