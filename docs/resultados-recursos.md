# Resultados — Consumo de CPU e memória

**Data:** 05/07/2026
**Ferramenta:** `kubectl top pods` (metrics-server), amostragem a cada 5 s
**Ambiente:** cluster Kubernetes local (Docker Desktop), namespace `agro-saas`

O script `scripts/monitor_k8s.sh` grava, em CSV, uma amostra por pod a cada 5 s
com CPU (millicores) e memória (MiB). Os arquivos brutos estão em
`docs/locust_runs/monitor_{10,50,100}.csv`; o script `scripts/run_all_loadtests_incluster.sh`
dispara o monitor em paralelo a cada cenário Locust.

## 1. Resumo por cenário

| Cenário | Componente | CPU (m — média / mediana / máx) | Memória (MiB — média / mediana / máx) | Observação |
|---|---|---:|---:|---|
| Sem carga (baseline) | django-api (3 pods) | 7 / 9 / 10 | 102 / 103 / 103 | HPA em `cpu: 10 %/70 %` (2–10 réplicas) |
| Sem carga (baseline) | postgres            | 10 / 10 / 10 | 23 / 23 / 23 | Idle |
| 10 usuários | django-api (3 pods)         | 39 / 32 / 100 | 114 / 115 / 115 | 796 req, 0 % falha, HPA estável em 3 réplicas |
| 10 usuários | postgres                    | 52 / 57 / 66 | 24 / 23 / 26 | — |
| 50 usuários | django-api (3 → 5 pods)     | 99 / 75 / 367 | 115 / 115 / 117 | 3 704 req, 0 % falha; HPA sobe de 3 → 5 réplicas |
| 50 usuários | postgres                    | 170 / 197 / 250 | 24 / 23 / 34 | — |
| 100 usuários | django-api (5 → 9 → 10 pods) | 183 / 137 / 473 | 115 / 115 / 118 | 6 741 req, 0 % falha; HPA sobe 5 → 9 → 10 réplicas |
| 100 usuários | postgres                    | 414 / 403 / 749 | 25 / 24 / 28 | Postgres passa a ser o principal ponto de custo |
| locust-runner (in-cluster) | pod dedicado | 0 / 0 / 0 | 3 / 3 / 3 | Carga não vem do node local |

> As linhas de "média / mediana / máx" agregam TODAS as amostras de TODOS os
> pods do respectivo Deployment durante a janela do cenário. O aumento no
> "número de pods" ocorre porque o HPA cria réplicas adicionais durante o
> teste (as amostras novas entram no cálculo assim que o pod passa a reportar
> métricas).

## 2. Interpretação

- **Memória da aplicação é estável.** Cada pod `django-api` fica entre
  102–118 MiB independentemente da carga. Isso responde diretamente à crítica
  da banca sobre custo de memória: o custo marginal por réplica é modesto
  (~115 MiB) e não cresce sob pressão de requisições, apenas com o número
  de réplicas.
- **CPU escala aproximadamente com a carga.** O pico máximo em um único pod
  vai de 10 m (repouso) → 100 m (10 usuários) → 367 m (50 usuários) →
  473 m (100 usuários). Como o `resources.requests.cpu` do Deployment é
  100 m, um pod consumindo 473 m corresponde a 473 % do request — e é o que
  dispara o HPA (alvo: 70 %).
- **Postgres é o próximo gargalo.** No cenário de 100 usuários o pod
  `postgres-0` chega a **749 m** de CPU (média 414 m), enquanto os pods
  Django somados usam ~1 500 m entre 5–10 réplicas. Isso mostra, com
  evidência, que a próxima frente de otimização para o modelo
  schema-per-tenant é o banco (cache de conexões, `pgbouncer`, ou banco
  próprio por tenant grande) — informação útil para a seção de "trabalhos
  futuros" do TCC.
- **Locust-runner não distorce a medição.** O pod que dispara a carga
  consome apenas 3 MiB e 0 m de CPU (é um cliente HTTP com `wait_time`),
  então os números acima refletem quase inteiramente o custo de servir a
  aplicação.

## 3. Limitações da medição

- `kubectl top` reporta a taxa suavizada pelo metrics-server (janela de ~15 s),
  então valores muito rápidos podem ser subestimados. O `máx` observado é o
  maior valor de uma amostra de 5 s.
- Cluster local no Docker Desktop tem CPU/memória compartilhadas com o host —
  os números aqui são **indicativos** para o protótipo. Uma medição
  operacional exigiria cluster gerenciado (EKS/GKE/AKS) com hardware
  dedicado, workload sintético representativo e coleta contínua.
- Não foi possível popular `hpa_cpu_current` em todas as amostras porque o
  campo `.status.currentCPUUtilizationPercentage` do HPA aparece vazio em
  transições. Os valores efetivos de utilização estão registrados em
  `docs/locust_runs/hpa_snapshots.log` (antes/depois de cada cenário).
