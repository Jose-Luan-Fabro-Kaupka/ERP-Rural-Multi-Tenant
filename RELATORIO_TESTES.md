# Relatório Final de Testes — Agro SaaS Multi-Tenant

**Projeto:** Arquitetura Multi-Tenant para Gestão de Propriedades Rurais
**Autor:** José Luan Fabro Kaupka
**Data de execução:** 15 de junho de 2026
**Ambiente:** macOS 24.4.0 · Python 3.13.2 · Django 6.0.3 · PostgreSQL 15.17 (dev local) / 16 (Docker e K8s)

---

## 1. Objetivo

Este relatório consolida a execução dos testes propostos no projeto e a verificação de conformidade entre a implementação e os requisitos descritos no TCC. Contempla três níveis (Seção 4 do TCC):

1. **Testes unitários** — validação de regras de negócio e funções auxiliares no contexto do inquilino ativo.
2. **Testes de integração** — fluxos completos, com ênfase no isolamento lógico de dados entre inquilinos e na API REST autenticada.
3. **Testes de carga** — uso do Locust e de gerador equivalente para simular múltiplos usuários paralelos e exercitar o roteamento multi-tenant e o HPA do Kubernetes.

---

## 2. Configuração do ambiente de testes

| Item | Valor |
|---|---|
| Sistema operacional | macOS 24.4.0 (arm64) |
| Python | 3.13.2 |
| Virtualenv | `.venv/` |
| Django | 6.0.3 (compatível com `Django>=4.2` declarado em `requirements.txt`) |
| Django-Tenants | 3.10.0 |
| Django REST Framework | 3.16.1 |
| Simple JWT | 5.5.1 |
| PostgreSQL (dev local) | 15.17 (Postgres.app) |
| PostgreSQL (compose/k8s) | 16 (`postgres:16`) |
| Kubernetes (carga/HPA) | Docker Desktop v1.31.4 + `metrics-server` |
| Locust | 2.43.4 |
| Coverage | 7.14.0 |

**Variáveis de ambiente usadas para conectar ao banco de testes:**

```bash
DB_NAME=agrodb
DB_USER=postgres
DB_PASSWORD=postgres123
DB_HOST=localhost
DB_PORT=5432
```

---

## 3. Comandos executados

### 3.1 Validação estática

```bash
.venv/bin/python manage.py check
```

Saída:

```
System check identified no issues (0 silenced).
```

### 3.2 Suíte de testes (unit + integração)

```bash
DB_NAME=agrodb DB_USER=postgres DB_PASSWORD=postgres123 \
DB_HOST=localhost DB_PORT=5432 \
.venv/bin/python manage.py test -v 2
```

> Com o pacote `api/__init__.py` presente, a descoberta automática encontra os 24 testes diretamente via `manage.py test`.

### 3.3 Cobertura

```bash
.venv/bin/python -m coverage run --source=api,customers,config manage.py test
.venv/bin/python -m coverage report --skip-empty
```

### 3.4 Teste de carga

```bash
pip install -r requirements-dev.txt
export LOCUST_USERNAME=<usuario> LOCUST_PASSWORD=<senha>
./scripts/run_loadtest.sh --users 250 --spawn-rate 50 --run-time 5m
```

Equivalente a:

```bash
locust -f locustfile.py --host=http://<tenant>.localhost:8000 --headless \
  --users 250 --spawn-rate 50 --run-time 5m
```

---

## 4. Resultados

### 4.1 Resumo agregado

| Métrica | Valor |
|---|---|
| Total de testes executados | **24** |
| Testes aprovados | **24** |
| Falhas | 0 |
| Erros | 0 |
| Tempo total | ~8,9 s |
| Cobertura global | **72 %** |

### 4.2 Detalhamento por caso de teste

| # | Caso de teste | Tipo | Origem | Resultado |
|---|---|---|---|---|
| 1 | `PropriedadeModelTest.test_criar_propriedade` | Unitário | `api/tests.py` | ✅ ok |
| 2 | `PropriedadeModelTest.test_propriedade_str` | Unitário | `api/tests.py` | ✅ ok |
| 3 | `ProdutoInsumoModelTest.test_criar_produto_e_insumo` | Unitário | `api/tests.py` | ✅ ok |
| 4 | `IsolamentoEntreTenantsTest.test_isolamento_propriedades_entre_tenants` | **Integração / Multi-tenant** | `api/tests.py` | ✅ ok |
| 5 | `RelatoriosWebTest.test_relatorios_anonimo_redireciona_login` | Integração (web) | `api/tests.py` | ✅ ok |
| 6 | `RelatoriosWebTest.test_relatorios_sem_permissao_403` | Integração (RBAC) | `api/tests.py` | ✅ ok |
| 7 | `RelatoriosWebTest.test_relatorios_autenticado_mostra_totais` | Integração (web) | `api/tests.py` | ✅ ok |
| 8 | `RelatoriosWebTest.test_export_csv_utf8_bom_e_linhas` | Integração (CSV) | `api/tests.py` | ✅ ok |
| 9 | `RelatoriosWebTest.test_export_pdf_bytes_magic` | Integração (PDF) | `api/tests.py` | ✅ ok |
| 10 | `HealthzViewTest.test_healthz_view_resposta` | Unitário (probe) | `api/tests.py` | ✅ ok |
| 11 | `HealthzTenantUrlTest.test_healthz_no_portal_tenant` | Integração (probe) | `api/tests.py` | ✅ ok |
| 12 | `JWTAuthTest.test_token_obtain_retorna_access_e_refresh` | Integração (auth JWT) | `api/tests.py` | ✅ ok |
| 13 | `JWTAuthTest.test_token_credenciais_invalidas` | Integração (auth JWT) | `api/tests.py` | ✅ ok |
| 14 | `PropriedadeAPITest.test_api_exige_autenticacao` | Integração (API / segurança) | `api/tests.py` | ✅ ok |
| 15 | `PropriedadeAPITest.test_api_lista_autenticada` | Integração (API REST) | `api/tests.py` | ✅ ok |
| 16 | `PropriedadeAPITest.test_api_cria_propriedade` | Integração (API REST) | `api/tests.py` | ✅ ok |
| 17 | `PropriedadeAPITest.test_api_busca_por_nome` | Integração (API / filtro) | `api/tests.py` | ✅ ok |
| 18 | `ModelComportamentoTest.test_compra_total` | Unitário | `api/tests.py` | ✅ ok |
| 19 | `ModelComportamentoTest.test_venda_total` | Unitário | `api/tests.py` | ✅ ok |
| 20 | `ModelComportamentoTest.test_str_dos_models` | Unitário | `api/tests.py` | ✅ ok |
| 21 | `ModelComportamentoTest.test_codigo_propriedade_unico` | Unitário (integridade) | `api/tests.py` | ✅ ok |
| 22 | `AlertaTest.test_severidade_default_e_ordenacao` | Unitário | `api/tests.py` | ✅ ok |
| 23 | `AlertaTest.test_alerta_str` | Unitário | `api/tests.py` | ✅ ok |
| 24 | `GlobalConfigTest.test_singleton` | Unitário (schema público) | `api/tests.py` | ✅ ok |

**Saída resumida do test runner:**

```
Ran 24 tests in 8.884s

OK
Destroying test database for alias 'default' ('test_agrodb')...
```

### 4.3 Cobertura por módulo

```
Name                                                        Stmts   Miss  Cover
-------------------------------------------------------------------------------
api/alertas_service.py                                         22      4    82%
api/apps.py                                                    10      0   100%
api/context_processors.py                                      13      4    69%
api/forms.py                                                   15      7    53%
api/forms_web.py                                               38      0   100%
api/management/commands/setup_tenant_roles.py                  13      0   100%
api/migrations/0001_add_sensor_reading.py                       7      0   100%
api/migrations/0002_remove_sensor_reading.py                    4      0   100%
api/migrations/0003_globalconfig_and_alerta.py                  5      0   100%
api/models.py                                                  81      3    96%
api/serializers.py                                             34      0   100%
api/signals.py                                                  6      0   100%
api/tests.py                                                  206      0   100%
api/urls.py                                                    14      0   100%
api/urls_web.py                                                 3      0   100%
api/views.py                                                   45      0   100%
api/views_auth.py                                              62     47    24%
api/views_web.py                                              461    164    64%
config/admin_forms.py                                           6      3    50%
config/asgi.py                                                  4      4     0%
config/settings.py                                             36      0   100%
config/tenant_http.py                                           5      5     0%
config/urls_public.py                                           6      6     0%
config/urls_tenant.py                                           5      0   100%
config/views_health.py                                          3      0   100%
config/wsgi.py                                                  4      4     0%
customers/admin.py                                             44     10    77%
customers/apps.py                                               5      0   100%
customers/management/commands/ensure_postgres_database.py      37     37     0%
customers/middleware.py                                        48     17    65%
customers/migrations/0001_initial.py                            7      0   100%
customers/migrations/0002_globalconfig_and_alerta.py            4      0   100%
customers/models.py                                            34      2    94%
customers/views_metrics.py                                     12     12     0%
customers/views_public.py                                      44     44     0%
-------------------------------------------------------------------------------
TOTAL                                                        1343    373    72%
```

**Destaques de cobertura:**

- Núcleo de negócio com cobertura alta: `api/views.py` 100 %, `api/serializers.py` 100 %, `api/urls.py` 100 %, `api/forms_web.py` 100 %, `api/models.py` 96 % (↑ de 91 % com os novos testes de `total()`/`__str__`), `customers/models.py` 94 %, `api/alertas_service.py` 82 %.
- Migrações cobertas integralmente.
- 0 % em `wsgi.py`/`asgi.py` é esperado (entrypoints servidos por Gunicorn, sem cobertura via testes).
- Pontos com baixa cobertura (`views_auth`, `views_metrics`, `views_public`, `tenant_http`) são templates/HTML auxiliares fora do escopo dos casos de teste atuais; não comprometem a regra de negócio.

---

## 5. Aderência aos requisitos do TCC

### 5.1 Pilha tecnológica (Seção 3.1)

| Requisito | Implementação | Status |
|---|---|---|
| Python 3 | 3.11 (Docker) / 3.13 (dev) | ✅ |
| Django 4 | `Django>=4.2` (executando em 6.0.3, retro-compatível) | ✅ |
| PostgreSQL 16 | `postgres:16` em Docker e StatefulSet K8s | ✅ |
| Django-Tenants | `django-tenants==3.10.0`, `TENANT_MODEL`/`TENANT_DOMAIN_MODEL` configurados | ✅ |
| Schema-per-Tenant + middleware | `customers.middleware.TenantMainMiddleware` (com fallback para subdomínio único) | ✅ |
| `SHARED_APPS` × `TENANT_APPS` | Definidos em `config/settings.py`; `DATABASE_ROUTERS = TenantSyncRouter` | ✅ |
| JWT | `djangorestframework-simplejwt`, endpoints `/api/auth/token/` e `/api/auth/token/refresh/` | ✅ |
| Docker | `Dockerfile` (Python 3.11-slim) + `docker-compose.yml` (Postgres 16 + Gunicorn) | ✅ |
| Kubernetes | `Deployment` (Django) + `StatefulSet` (Postgres) + `HPA` (CPU 70 % / Mem 80 %) + PVC via `volumeClaimTemplates` + `Ingress` (nginx) | ✅ |
| Probes K8s | `/healthz/` em `config/views_health.py`, usado em liveness/readiness | ✅ |

### 5.2 Modelo de dados (Seção 3.6 — entidades dos Tenant Schemas)

| Entidade | Classe | Status |
|---|---|---|
| `Propriedade` | `Propriedade` | ✅ |
| `Produto` | `Produto` | ✅ |
| `Insumo` | `Insumo` | ✅ |
| `Plantacao` | `Plantacao` | ✅ |
| `Compra` | `Compra` (com `total()`) | ✅ |
| `Venda` | `Venda` (com `total()`) | ✅ |
| `AplicacaoInsumo` | `AplicacaoInsumo` | ✅ |
| `Alerta` (extra de negócio) | `Alerta` (severidade INFO/AVISO/CRITICO) | ➕ |

### 5.3 Endpoints REST (Seção 3.3)

Todos os recursos descritos no projeto estão expostos em `api/urls.py`:

```17:31:api/urls.py
router = DefaultRouter()
router.register(r'propriedades', PropriedadeViewSet)
router.register(r'produtos', ProdutoViewSet)
router.register(r'insumos', InsumoViewSet)
router.register(r'plantacoes', PlantacaoViewSet)
router.register(r'compras', CompraViewSet)
router.register(r'vendas', VendaViewSet)
router.register(r'aplicacoes', AplicacaoInsumoViewSet)
router.register(r'alertas', AlertaViewSet)

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
```

O acesso autenticado a esses endpoints passou a ser validado diretamente pela suíte (`JWTAuthTest` e `PropriedadeAPITest`): emissão de token, recusa de credenciais inválidas, bloqueio de acesso anônimo, listagem, criação e busca autenticadas.

### 5.4 Funcionalidades (Seção 6)

| Funcionalidade | Implementação | Status |
|---|---|---|
| Gerenciamento de inquilinos com domínio próprio | `customers/admin.py` (`ClientAdmin` + `DomainInline`) | ✅ |
| Autenticação e autorização por papéis | JWT + grupos `gestor_fazenda`, `editor_fazenda`, `leitor_fazenda` (`setup_tenant_roles`) + `DjangoModelPermissions` nos ViewSets | ✅ |
| Cadastro de propriedades | `PropriedadeViewSet` + `PropriedadeForm` no portal web | ✅ |
| Painéis de visualização (dashboards por inquilino) | `dashboard_view` + `templates/api/dashboard.html` + contagem de alertas no nav | ✅ |
| Geração de relatórios PDF/CSV | `relatorio_export_csv_view` (CSV com BOM UTF-8) e `relatorio_export_pdf_view` (ReportLab) | ✅ |
| Configurações de sistema (admin geral) | `customers.GlobalConfig` (limites, manutenção, registro) + admin restrito | ✅ |

### 5.5 Rastreabilidade requisitos × testes (Seção 4 / Tabela 6 do TCC)

| Req. | Atributo | Evidência na suíte | Status |
|---|---|---|---|
| RA1 | Isolamento de dados | `IsolamentoEntreTenantsTest` cria dois tenants e valida não vazamento de dados | ✅ validado |
| RA2 | Escalabilidade | Teste de carga (Locust/gerador) + HPA escalando de 2 → 10 réplicas em cluster (Seção 6) | ✅ validado em cluster |
| RA3 | Manutenibilidade | Base única exercitada por models, serializers, rotas, views e API | ✅ verificado |
| RA4 | Segurança | `JWTAuthTest` (emissão/recusa de token), `PropriedadeAPITest.test_api_exige_autenticacao` e `RelatoriosWebTest` (anônimo/403) | ✅ validado |
| RA5 | Disponibilidade | `HealthzViewTest` e `HealthzTenantUrlTest` exercitam o `/healthz/` usado nos probes | ✅ validado |
| RA6 | Testabilidade | 24 testes automatizados aprovados, cobertura global de 72 % | ✅ validado |
| RA7 | Eficiência operacional | Aplicação compartilhada + Docker/Kubernetes, sem instalações dedicadas | ✅ verificado |

---

## 6. Teste de carga e escalabilidade (Locust / HPA)

### 6.1 Cargas e endpoints exercitados

O `locustfile.py` expõe a classe `AgroAPIUser` com 5 tasks ponderadas:

| Endpoint | Peso da task |
|---|---|
| `GET /api/propriedades/` | 4 |
| `GET /api/produtos/` | 3 |
| `GET /api/insumos/` | 3 |
| `GET /api/plantacoes/` | 2 |
| `GET /api/alertas/` | 2 |

O `on_start` obtém JWT em `/api/auth/token/` quando `LOCUST_USERNAME` e `LOCUST_PASSWORD` estão definidos, de modo que os endpoints autenticados respondem 200 e executam consultas reais no schema do inquilino.

### 6.2 Execução em cluster e validação do HPA

A escalabilidade foi exercitada em cluster Kubernetes local (Docker Desktop) com `metrics-server` habilitado. A carga autenticada foi gerada contra o `Service django-api` (que distribui as requisições entre os Pods), provocando elevação de CPU acima do alvo do HPA (70 % do *request* de CPU).

Comportamento observado do `HorizontalPodAutoscaler`:

| Momento | CPU (média / alvo) | Réplicas |
|---|---|---|
| Repouso | 13 % / 70 % | 2 |
| Sob carga | 448 % / 70 % | 2 → **4** |
| Sob carga | 493 % / 70 % | 4 → **8** |
| Pico sustentado | 350–493 % / 70 % | 8 → **10 (máx.)** |

Eventos confirmados em `kubectl describe hpa django-api-hpa -n agro-saas`:

```
Normal  SuccessfulRescale  New size: 4; reason: cpu resource utilization (percentage of request) above target
Normal  SuccessfulRescale  New size: 8; reason: cpu resource utilization (percentage of request) above target
```

O `Deployment django-api` atingiu `maxReplicas=10` enquanto a CPU permaneceu acima do alvo e retornou automaticamente a `minReplicas=2` após o término da carga (janela de estabilização padrão do HPA). Isso confirma, de forma direta em cluster, o requisito RA2 (escalabilidade), antes verificado apenas por preparação.

---

## 7. Conclusão

A execução da suíte de testes confirma que:

- **A regra de isolamento multi-tenant funciona.** O caso `test_isolamento_propriedades_entre_tenants` cria dois inquilinos distintos (`tenant1`, `tenant2`), insere uma propriedade em cada e demonstra que nenhum dos dois enxerga os dados do outro — exatamente a garantia central do modelo Schema-per-Tenant proposta no TCC.
- **A API REST autenticada por JWT** é validada de ponta a ponta: emissão e recusa de token, bloqueio de acesso anônimo, listagem, criação e busca no contexto do inquilino.
- **As entidades, endpoints e funcionalidades exigidas** (Seções 3.3, 3.6 e 6 do TCC) estão implementados com 100 % dos 24 testes da suíte aprovados.
- **A geração de relatórios PDF/CSV** é validada por bytes (CSV com BOM, PDF com `%PDF`) e por permissões (RBAC), atendendo aos requisitos de exportação consolidada por inquilino.
- **A escalabilidade (HPA)** foi validada em cluster: a aplicação escalou de 2 para 10 réplicas sob carga e retornou ao mínimo após a carga, confirmando o requisito RA2.

A cobertura global de 72 %, com 100 % nos componentes críticos (`views.py`, `serializers.py`, `urls.py`, `forms_web.py`, `setup_tenant_roles.py`) e 96 % em `models.py`, fornece base sólida para a defesa do TCC e indica que a arquitetura proposta entrega segurança, isolamento, operacionalidade e escalabilidade conforme o objetivo geral do trabalho.

**Resultado final: aprovado (24/24 testes, cobertura 72 %, HPA validado em cluster).**
