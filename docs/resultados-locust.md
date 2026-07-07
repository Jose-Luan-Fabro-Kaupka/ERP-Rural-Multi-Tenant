# Resultados — Teste de carga com Locust

**Data:** 05/07/2026
**Ferramenta:** Locust 2.43.4
**Modo de execução:** in-cluster (Pod `locust-runner` no namespace `agro-saas`),
disparando requisições contra o Service `django-api.agro-saas.svc.cluster.local`.

O Pod `locust-runner` foi criado pelo manifesto
`scripts/locust-in-cluster.yaml`, com o `locustfile.py` montado por ConfigMap.
Os cenários foram orquestrados pelo script
`scripts/run_all_loadtests_incluster.sh` via `kubectl exec` — eliminando o
gargalo do `kubectl port-forward` observado nos ensaios anteriores.

## 1. Configuração comum

- **Endpoints exercitados** (`locustfile.py`), com pesos:
  `GET /api/propriedades/` (4), `GET /api/produtos/` (3),
  `GET /api/insumos/` (3), `GET /api/plantacoes/` (2),
  `GET /api/alertas/` (2), além de `POST /api/auth/token/` no `on_start`.
- **Autenticação:** JWT emitido no `on_start` para o usuário `locust` do tenant
  `loadtest` (variáveis `LOCUST_USERNAME`, `LOCUST_PASSWORD`).
- **Roteamento multi-tenant:** header `Host: loadtest.localhost` fixado por
  `LOCUST_TENANT_HOST` (o Service é resolvido pela ClusterIP).
- **`wait_time`:** `between(0.5, 2.5)` (delay aleatório entre requisições).
- **Duração de cada cenário:** 2 minutos.
- **Cool-down entre cenários:** 30 s (para estabilizar a janela do HPA).

## 2. Resumo agregado

| Usuários | Duração | Req. totais | Req/s | Falhas | Mediana | Média | p95 | p99 | Máx |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **10**  | 2 min | 796  | 6,67  | **0 (0,00 %)** | 19 ms | 36 ms  | 44 ms   | 730 ms  | 1 535 ms |
| **50**  | 2 min | 3 704 | 31,01 | **0 (0,00 %)** | 15 ms | 76 ms  | 150 ms  | 2 100 ms | 3 783 ms |
| **100** | 2 min | 6 741 | 56,40 | **0 (0,00 %)** | 21 ms | 228 ms | 1 100 ms | 3 500 ms | 8 494 ms |

> Fonte primária: `docs/locust_runs/locust_{10,50,100}_stats.csv` (linha
> `Aggregated`). Os históricos de série temporal estão em
> `locust_{10,50,100}_stats_history.csv`.

Todas as 11 241 requisições foram bem-sucedidas em HTTP 200, sem *timeouts* nem
falhas de conexão — comportamento diferente do ensaio via `kubectl
port-forward`, onde 50/100 usuários geravam 98 % de `ConnectionRefusedError`
(gargalo do túnel SPDY, não da aplicação).

## 3. Detalhamento por rota (cenário 100 usuários)

| Rota | # req | Mediana | Média | p95 | Req/s |
|---|---:|---:|---:|---:|---:|
| `GET /api/propriedades/` | 1 898 | 21 ms | 186 ms | 920 ms | 15,88 |
| `GET /api/insumos/`       | 1 497 | 20 ms | 184 ms | 890 ms | 12,52 |
| `GET /api/produtos/`      | 1 351 | 22 ms | 186 ms | 910 ms | 11,30 |
| `GET /api/alertas/`       | 978   | 20 ms | 189 ms | 830 ms | 8,18 |
| `GET /api/plantacoes/`    | 917   | 20 ms | 186 ms | 880 ms | 7,67 |
| `POST /api/auth/token/`   | 100   | 2 500 ms | 3 036 ms | 8 100 ms | 0,84 |

O custo desproporcional do `POST /api/auth/token/` é esperado: envolve
`bcrypt`/PBKDF2 no `django.contrib.auth`, e cada usuário Locust emite apenas
um token no `on_start`. As rotas GET, que representam >98 % do tráfego,
mantêm mediana ≤22 ms mesmo com 100 clientes simultâneos.

## 4. Como reproduzir

```bash
# 1. Ajustar tenant/usuário do teste
kubectl -n agro-saas exec deployment/django-api -- python manage.py shell -c "
from django_tenants.utils import get_tenant_model, tenant_context
from django.contrib.auth import get_user_model
T = get_tenant_model()
t, _ = T.objects.get_or_create(schema_name='loadtest', defaults={'name': 'Load Test'})
# ... criar Domain 'loadtest.localhost' e usuário 'locust/locust123' ...
"

# 2. Rodar os 3 cenários (~8 min no total)
./scripts/run_all_loadtests_incluster.sh 2m
```

Os artefatos (CSVs, logs, HPA snapshots) ficam em `docs/locust_runs/`.

## 5. Observações

- O ganho em `req/s` de 10 → 100 usuários (6,67 → 56,40) mostra escalabilidade
  quase linear até o ponto em que o HPA está estabilizando novas réplicas.
- O aumento no p95/p99 do cenário de 100 usuários é coerente com o processo
  de ramp-up: enquanto o HPA cria novos Pods (5 → 9 → 10), a fila de
  requisições ainda passa pelos poucos Pods existentes, gerando caudas mais
  longas. Ver `docs/resultados-hpa.md`.
- 0 % de falhas em todos os cenários é o argumento mais forte para a banca:
  a aplicação multi-tenant respondeu 200 em 100 % das 11 241 requisições
  autenticadas, mesmo com o cluster passando por auto-scaling.
