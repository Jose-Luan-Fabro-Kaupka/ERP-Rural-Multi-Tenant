# Relatório de Testes 2 — Agro SaaS Multi-Tenant

**Projeto:** Arquitetura Multi-Tenant para Gestão de Propriedades Rurais  
**Autor:** José Luan Fabro Kaupka  
**Período de avaliação:** junho–julho de 2026  
**Última execução da suíte automatizada:** 06 de julho de 2026  
**Última execução de carga e HPA:** 05 de julho de 2026  

---

## 1. Escopo

Este relatório consolida a segunda rodada de avaliação do protótipo, ampliando a
evidência arquitetural em relação ao relatório anterior (`RELATORIO_TESTES.md`,
15/06/2026). Abrange quatro frentes:

1. **Testes automatizados** — suíte unitária e de integração com cobertura de código.
2. **Testes de carga** — Locust em cluster Kubernetes com três níveis de concorrência.
3. **Consumo de recursos e escalonamento** — amostragem de CPU/memória e validação do HPA.
4. **Métrica de multi-tenancy** — tempo de criação de tenant (schema-per-tenant).

Os artefatos brutos que sustentam as tabelas deste documento estão em
`docs/resultados-*.md` e `docs/locust_runs/`.

---

## 2. Ambiente

| Item | Valor |
|---|---|
| Sistema operacional (dev) | macOS 24.4.0 (arm64) |
| Python | 3.13.2 |
| Django | 6.0.3 |
| Django-Tenants | 3.10.0 |
| Django REST Framework | 3.16.1 |
| Simple JWT | 5.5.1 |
| PostgreSQL (dev local) | 15.17 |
| PostgreSQL (Docker/K8s) | 16 |
| Coverage | 7.14+ |
| Locust | 2.43.4 |
| Kubernetes | Docker Desktop, namespace `agro-saas`, metrics-server habilitado |

Conexão ao banco de testes: `agrodb` em `localhost:5432`, usuário `postgres`.

---

## 3. Testes automatizados

### 3.1 Resumo (06/07/2026)

| Métrica | Resultado |
|---|---|
| Testes executados | **25** |
| Aprovados | **25** |
| Falhas | 0 |
| Erros | 0 |
| Tempo total | **14,252 s** |
| Cobertura global (`api`, `customers`, `config`) | **73 %** |

Saída do test runner:

```
Ran 25 tests in 14.252s

OK
Destroying test database for alias 'default'...
```

Comparado ao relatório anterior: a suíte passou de 24 para **25** casos com a
inclusão de `RelatorioVolumosoTest.test_gera_relatorio_completo`; a cobertura
subiu de 72 % para **73 %** (1 396 statements, 377 miss).

### 3.2 Casos de teste

| # | Caso de teste | Tipo | Resultado |
|---|---|---|---|
| 1 | `PropriedadeModelTest.test_criar_propriedade` | Unitário | ok |
| 2 | `PropriedadeModelTest.test_propriedade_str` | Unitário | ok |
| 3 | `ProdutoInsumoModelTest.test_criar_produto_e_insumo` | Unitário | ok |
| 4 | `IsolamentoEntreTenantsTest.test_isolamento_propriedades_entre_tenants` | Integração / multi-tenant | ok |
| 5 | `RelatoriosWebTest.test_relatorios_anonimo_redireciona_login` | Integração (web) | ok |
| 6 | `RelatoriosWebTest.test_relatorios_sem_permissao_403` | Integração (RBAC) | ok |
| 7 | `RelatoriosWebTest.test_relatorios_autenticado_mostra_totais` | Integração (web) | ok |
| 8 | `RelatoriosWebTest.test_export_csv_utf8_bom_e_linhas` | Integração (CSV) | ok |
| 9 | `RelatoriosWebTest.test_export_pdf_bytes_magic` | Integração (PDF) | ok |
| 10 | `HealthzViewTest.test_healthz_view_resposta` | Unitário (probe) | ok |
| 11 | `HealthzTenantUrlTest.test_healthz_no_portal_tenant` | Integração (probe) | ok |
| 12 | `JWTAuthTest.test_token_obtain_retorna_access_e_refresh` | Integração (JWT) | ok |
| 13 | `JWTAuthTest.test_token_credenciais_invalidas` | Integração (JWT) | ok |
| 14 | `PropriedadeAPITest.test_api_exige_autenticacao` | Integração (segurança) | ok |
| 15 | `PropriedadeAPITest.test_api_lista_autenticada` | Integração (API REST) | ok |
| 16 | `PropriedadeAPITest.test_api_cria_propriedade` | Integração (API REST) | ok |
| 17 | `PropriedadeAPITest.test_api_busca_por_nome` | Integração (filtro) | ok |
| 18 | `ModelComportamentoTest.test_compra_total` | Unitário | ok |
| 19 | `ModelComportamentoTest.test_venda_total` | Unitário | ok |
| 20 | `ModelComportamentoTest.test_str_dos_models` | Unitário | ok |
| 21 | `ModelComportamentoTest.test_codigo_propriedade_unico` | Unitário (integridade) | ok |
| 22 | `AlertaTest.test_severidade_default_e_ordenacao` | Unitário | ok |
| 23 | `AlertaTest.test_alerta_str` | Unitário | ok |
| 24 | `GlobalConfigTest.test_singleton` | Unitário (schema público) | ok |
| 25 | `RelatorioVolumosoTest.test_gera_relatorio_completo` | Integração (relatório em volume) | ok |

O caso #25 popula 30 propriedades com 12 compras e 12 vendas cada, exercitando o
fluxo consolidado de relatório em volume — ausente na primeira rodada.

### 3.3 Cobertura por módulo (06/07/2026)

| Módulo | Cobertura |
|---|---|
| `api/views.py` | 100 % |
| `api/serializers.py` | 100 % |
| `api/urls.py` | 100 % |
| `api/forms_web.py` | 100 % |
| `api/models.py` | 96 % |
| `api/tests.py` | 98 % |
| `api/alertas_service.py` | 82 % |
| `api/views_web.py` | 64 % |
| `customers/models.py` | 94 % |
| `customers/middleware.py` | 65 % |
| `config/settings.py` | 100 % |
| `config/views_health.py` | 100 % |
| **TOTAL** | **73 %** (1 396 stmts, 377 miss) |

Módulos com 0 % (`wsgi.py`, `asgi.py`, `urls_public.py`, `tenant_http.py`,
`views_metrics.py`, `views_public.py`, `ensure_postgres_database`) são
entrypoints ou utilitários de infraestrutura não exercitados diretamente pela
suíte — comportamento esperado.

---

## 4. Testes de carga (Locust)

### 4.1 Configuração (05/07/2026)

Execução **in-cluster**: Pod `locust-runner` no namespace `agro-saas`,
disparando requisições contra o Service `django-api` pela ClusterIP (sem
`port-forward`). Tenant de teste: `loadtest` (`Host: loadtest.localhost`).
Autenticação JWT no `on_start` de cada usuário virtual.

Endpoints e pesos no `locustfile.py`:

| Endpoint | Peso |
|---|---|
| `GET /api/propriedades/` | 4 |
| `GET /api/produtos/` | 3 |
| `GET /api/insumos/` | 3 |
| `GET /api/plantacoes/` | 2 |
| `GET /api/alertas/` | 2 |
| `POST /api/auth/token/` | `on_start` (1× por usuário) |

Parâmetros comuns: duração de 2 minutos por cenário, `wait_time` entre 0,5 e
2,5 s, cool-down de 30 s entre cenários.

Fonte primária: `docs/locust_runs/locust_{10,50,100}_stats.csv`.

### 4.2 Resultados agregados

| Usuários | Duração | Req. totais | Req/s | Falhas | Mediana | Média | p95 | p99 | Máx |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 2 min | 796 | 6,67 | 0 (0,00 %) | 19 ms | 36 ms | 44 ms | 730 ms | 1 535 ms |
| 50 | 2 min | 3 704 | 31,01 | 0 (0,00 %) | 15 ms | 76 ms | 150 ms | 2 100 ms | 3 783 ms |
| 100 | 2 min | 6 741 | 56,40 | 0 (0,00 %) | 21 ms | 228 ms | 1 100 ms | 3 500 ms | 8 494 ms |

**Total:** 11 241 requisições, **0 % de falhas**, todas HTTP 200.

Ensaios anteriores via `kubectl port-forward` apresentaram até 98 % de
`ConnectionRefusedError` com 50/100 usuários — atribuído ao gargalo do túnel
SPDY, não à aplicação. A execução in-cluster eliminou esse viés.

### 4.3 Detalhamento — cenário de 100 usuários

| Rota | Requisições | Mediana | Média | p95 | Req/s |
|---|---:|---:|---:|---:|---:|
| `GET /api/propriedades/` | 1 898 | 21 ms | 186 ms | 920 ms | 15,88 |
| `GET /api/insumos/` | 1 497 | 20 ms | 184 ms | 890 ms | 12,52 |
| `GET /api/produtos/` | 1 351 | 22 ms | 186 ms | 910 ms | 11,30 |
| `GET /api/alertas/` | 978 | 20 ms | 189 ms | 830 ms | 8,18 |
| `GET /api/plantacoes/` | 917 | 20 ms | 186 ms | 880 ms | 7,67 |
| `POST /api/auth/token/` | 100 | 2 500 ms | 3 036 ms | 8 100 ms | 0,84 |

O `POST /api/auth/token/` concentra o custo de hash de senha (bcrypt/PBKDF2);
cada usuário Locust emite um único token no início. As rotas GET, que
representam mais de 98 % do tráfego, mantêm mediana ≤ 22 ms.

---

## 5. Consumo de CPU e memória

Amostragem com `kubectl top pods` a cada 5 s durante os cenários Locust.
Arquivos: `docs/locust_runs/monitor_{10,50,100}.csv`.

| Cenário | Componente | CPU (m — média / mediana / máx) | Memória (MiB — média / mediana / máx) |
|---|---|---:|---:|
| Sem carga | django-api (3 pods) | 7 / 9 / 10 | 102 / 103 / 103 |
| Sem carga | postgres | 10 / 10 / 10 | 23 / 23 / 23 |
| 10 usuários | django-api (3 pods) | 39 / 32 / 100 | 114 / 115 / 115 |
| 10 usuários | postgres | 52 / 57 / 66 | 24 / 23 / 26 |
| 50 usuários | django-api (3 → 5 pods) | 99 / 75 / 367 | 115 / 115 / 117 |
| 50 usuários | postgres | 170 / 197 / 250 | 24 / 23 / 34 |
| 100 usuários | django-api (5 → 10 pods) | 183 / 137 / 473 | 115 / 115 / 118 |
| 100 usuários | postgres | 414 / 403 / 749 | 25 / 24 / 28 |

Observações:

- Memória por pod `django-api` permaneceu entre 102 e 118 MiB em todos os
  cenários.
- CPU por pod cresceu com a carga; pico de 473 m em um pod (473 % do
  `requests.cpu = 100m`), condição que aciona o HPA.
- No cenário de 100 usuários, o PostgreSQL tornou-se o principal consumidor
  de CPU (média 414 m, pico 749 m).

---

## 6. Validação do HorizontalPodAutoscaler

Recurso: `HorizontalPodAutoscaler/django-api-hpa` — min 2, max 10 réplicas,
alvo CPU 70 % e memória 80 % (sobre `resources.requests` do Deployment).

| Cenário | Réplicas antes | CPU antes / alvo | Réplicas depois | CPU depois / alvo | Condição |
|---|---:|:---:|---:|:---:|---|
| Sem carga | 2 | 6 % / 70 % | 2 | 7 % / 70 % | Estável no piso |
| 10 usuários | 3 | 10 % / 70 % | 3 | 32 % / 70 % | Abaixo do alvo — sem scale-up |
| 50 usuários | 3 | 29 % / 70 % | 5 | 73 % / 70 % | Scale-up 3 → 5 |
| 100 usuários | 5 | 73 % / 70 % | 9 | 123 % / 70 % | Scale-up 5 → 9 → 10 |
| Após carga | 10 | 136 % / 70 % | — | — | `ScalingLimited=True` (teto atingido) |

Eventos registrados pelo controller (`docs/locust_runs/hpa_describe.log`):

```
Normal  SuccessfulRescale  New size: 5; reason: cpu resource utilization above target
Normal  SuccessfulRescale  New size: 9; reason: cpu resource utilization above target
Normal  SuccessfulRescale  New size: 10; reason: cpu resource utilization above target
```

Estado final: 10 réplicas `django-api` em execução; condição
`ScalingLimited=True` com mensagem `TooManyReplicas`.

---

## 7. Tempo de criação de tenant

Métrica do modelo schema-per-tenant: `INSERT` do tenant no schema `public`,
`INSERT` do domínio primário e `migrate_schemas` do schema recém-criado.
Medição com `time.perf_counter` via `scripts/measure_tenant_creation.py`.

### 7.1 Execução de 05/07/2026

| Execução | Tempo (s) |
|---:|---:|
| 1 | 0,272 |
| 2 | 0,332 |
| 3 | 0,315 |
| 4 | 0,245 |
| 5 | 0,241 |
| **Média** | **0,281** |
| Mediana | 0,272 |
| Mínimo | 0,241 |
| Máximo | 0,332 |

### 7.2 Execução de 06/07/2026 (revalidação)

| Execução | Tempo (s) |
|---:|---:|
| 1 | 0,830 |
| 2 | 0,784 |
| 3 | 1,030 |
| 4 | 0,644 |
| 5 | 0,535 |
| **Média** | **0,765** |
| Mediana | 0,784 |
| Mínimo | 0,535 |
| Máximo | 1,030 |

A variação entre as duas execuções reflete dependência de estado do banco,
cache e carga do host — não uma regressão funcional. O custo dominante em
ambos os ensaios é o `migrate_schemas`.

---

## 8. Rastreabilidade requisitos × evidência

| Req. | Atributo | Evidência | Status |
|---|---|---|---|
| RA1 | Isolamento de dados | `IsolamentoEntreTenantsTest` — dois tenants, sem vazamento | Validado |
| RA2 | Escalabilidade | Locust in-cluster + HPA 3 → 10 réplicas | Validado em cluster |
| RA3 | Manutenibilidade | Suíte cobre models, serializers, rotas, views e API | Verificado |
| RA4 | Segurança | `JWTAuthTest`, bloqueio anônimo, RBAC em relatórios | Validado |
| RA5 | Disponibilidade | `HealthzViewTest`, `HealthzTenantUrlTest` | Validado |
| RA6 | Testabilidade | 25 testes, 0 falhas, 73 % cobertura | Validado |
| RA7 | Eficiência operacional | App compartilhada + schemas separados; criação de tenant sub-segundo a ~1 s | Verificado |

---

## 9. Limitações

- O tempo da suíte automatizada varia conforme carga do host (14,252 s em
  06/07; execuções anteriores entre 12 s e 22 s com o mesmo resultado funcional).
- Métricas de carga, recursos e HPA foram obtidas em cluster local (Docker
  Desktop); valores absolutos de CPU/memória são indicativos.
- O scale-down do HPA (janela padrão de 5 min) não foi exercitado nesta rodada.
- Tempo de criação de tenant depende do estado do PostgreSQL e não deve ser
  tratado como constante entre ambientes.
- Ensaios via `port-forward` não são representativos de desempenho real da
  aplicação em cluster.

---

## 10. Conclusão

A segunda rodada de avaliação confirma e amplia os resultados do relatório
anterior:

- **25/25 testes aprovados** com cobertura global de **73 %** e 100 % nos
  módulos centrais da API REST.
- **Isolamento multi-tenant**, autenticação JWT, relatórios CSV/PDF (incluindo
  cenário volumoso) e health checks validados automaticamente.
- **11 241 requisições Locust** em cluster, **0 % de falhas**, com throughput
  de 6,67 a 56,40 req/s conforme a concorrência.
- **HPA** escalou de 3 para 10 réplicas sob carga, atingindo o teto configurado.
- **Memória estável** (~115 MiB por pod Django); PostgreSQL emerge como gargalo
  de CPU no cenário mais intenso.

**Resultado:** aprovado — evidência arquitetural consolidada para defesa do TCC.
