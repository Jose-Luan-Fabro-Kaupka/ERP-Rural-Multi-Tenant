# Resultados — Validação do HorizontalPodAutoscaler

**Data:** 05/07/2026
**Cluster:** Kubernetes local (Docker Desktop) com metrics-server habilitado
**Recurso avaliado:** `HorizontalPodAutoscaler/django-api-hpa`
(namespace `agro-saas`)

## 1. Configuração do HPA (arquivo `k8s/hpa.yaml`)

- Referência: `Deployment/django-api`
- Réplicas: **min 2**, **max 10**
- Alvo: CPU 70 % (do `resources.requests.cpu = 100m`), memória 80 %

Comandos usados para inspeção durante os testes:

```bash
kubectl get hpa django-api-hpa -n agro-saas
kubectl describe hpa django-api-hpa -n agro-saas
kubectl get deploy django-api -n agro-saas
```

## 2. Observações por cenário

| Cenário | Réplicas antes | CPU antes / alvo | Réplicas depois | CPU depois / alvo | Condição observada |
|---|---:|:---:|---:|:---:|---|
| Sem carga         | 2  | 6 % / 70 %  | 2  | 7 % / 70 %  | Estado estável no piso do HPA. |
| 10 usuários       | 3  | 10 % / 70 % | 3  | 32 % / 70 % | Carga insuficiente para escalar — CPU permanece abaixo do alvo. |
| 50 usuários       | 3  | 29 % / 70 % | 5  | 73 % / 70 % | HPA cruza o alvo e escala **3 → 5** réplicas. |
| 100 usuários      | 5  | 73 % / 70 % | 9  | 123 % / 70 % | HPA escala **5 → 9** e depois **9 → 10 (máximo)**. |
| Estado logo após  | 10 | 136 % / 70 % | — | — | `ScalingLimited=True` (`TooManyReplicas`) — quer escalar além de 10, mas atingiu o teto. |

Os valores foram capturados pelas funções `-- HPA antes --` / `-- HPA depois --`
do script `scripts/run_all_loadtests_incluster.sh` e estão preservados em
`docs/locust_runs/hpa_snapshots.log`.

## 3. Eventos emitidos pelo controller

Trecho de `kubectl describe hpa django-api-hpa -n agro-saas` capturado ao final
da bateria (arquivo `docs/locust_runs/hpa_describe.log`):

```
Events:
  Type    Reason             Age    From                       Message
  ----    ------             ----   ----                       -------
  Normal  SuccessfulRescale  18m    horizontal-pod-autoscaler  New size: 4;  reason: cpu resource utilization above target
  Normal  SuccessfulRescale  17m    horizontal-pod-autoscaler  New size: 6;  reason: (metric fluctuation)
  Normal  SuccessfulRescale  13m    horizontal-pod-autoscaler  New size: 3;  reason: All metrics below target
  Normal  SuccessfulRescale  4m26s  horizontal-pod-autoscaler  New size: 5;  reason: cpu resource utilization above target  ← cenário 50 usuários
  Normal  SuccessfulRescale  86s    horizontal-pod-autoscaler  New size: 9;  reason: cpu resource utilization above target  ← cenário 100 usuários
  Normal  SuccessfulRescale  26s    horizontal-pod-autoscaler  New size: 10; reason: cpu resource utilization above target  ← cenário 100 usuários
```

Condições reportadas:

```
AbleToScale     True    SucceededRescale   the HPA controller was able to update the target scale to 10
ScalingActive   True    ValidMetricFound   the HPA was able to successfully calculate a replica count from cpu resource utilization
ScalingLimited  True    TooManyReplicas    the desired replica count is more than the maximum replica count
```

## 4. Estado final observado após o teste de 100 usuários

```
kubectl top pods -n agro-saas
NAME                          CPU(cores)   MEMORY(bytes)
django-api-6774b9b97d-42jgs   24m          114Mi
django-api-6774b9b97d-bsd6r   17m          117Mi
django-api-6774b9b97d-kd6ps   11m          115Mi
django-api-6774b9b97d-ncdj2   14m          102Mi
django-api-6774b9b97d-prc6l   13m          116Mi
django-api-6774b9b97d-pwx89   16m          116Mi
django-api-6774b9b97d-qjwsd   19m          117Mi
django-api-6774b9b97d-qw5qm   22m          114Mi
django-api-6774b9b97d-rwn2x   22m          114Mi
django-api-6774b9b97d-xmdbr   21m          117Mi
locust-runner                 0m           3Mi
postgres-0                    31m          22Mi
```

10 réplicas ativas do `django-api`, todas `Running`.

## 5. Interpretação

- **RA2 (escalabilidade) validado em cluster.** O HPA reagiu à carga
  progressiva do Locust exatamente como esperado: mantido estável abaixo do
  alvo (10 → 32 % em 10 usuários), escalou 3 → 5 quando o alvo foi cruzado
  (73 %), e chegou ao teto de 10 réplicas quando a utilização passou dos 100 %.
- O `ScalingLimited=True` no final é uma evidência positiva para a banca: a
  aplicação **queria escalar mais** (o cálculo do controller indicou mais que
  10 réplicas necessárias) e o teto foi atingido por configuração — o
  aumento de `maxReplicas` no `k8s/hpa.yaml` é imediato (linha única) se a
  produção exigir.
- Sem `metrics-server` habilitado, os campos `TARGETS` e `.status.currentCPU…`
  ficam vazios e o HPA não escala. Isso ocorre em clusters "cru" e é o
  motivo pelo qual a validação foi feita em cluster local (Docker Desktop
  com metrics-server), e não com `minikube` sem addon.

## 6. Como reproduzir

```bash
# 1. aplicar todos os manifests
kubectl apply -f k8s/

# 2. confirmar HPA + metrics-server
kubectl get hpa django-api-hpa -n agro-saas
kubectl top pods -n agro-saas

# 3. gerar carga (in-cluster para evitar gargalo do port-forward)
./scripts/run_all_loadtests_incluster.sh 2m

# 4. observar durante a carga (em outro terminal)
kubectl get hpa -n agro-saas -w
kubectl get pods -n agro-saas -w
```

## 7. Limitações

- O teste foi conduzido em cluster local (Docker Desktop); em cluster
  gerenciado o comportamento é qualitativamente o mesmo, mas os limiares
  absolutos (CPU/memória) refletirão o hardware.
- Cool-downs de scale-down do HPA (janela padrão de 5 min) não foram
  exercitados neste roteiro — o objetivo aqui foi validar o *scale-up*.
- `resources.requests.cpu = 100m` foi mantido conforme o manifest atual.
  Ajustar esse valor muda o denominador do HPA e, portanto, o ponto em que
  o auto-scaling é acionado.
