# Resultados dos Testes Automatizados

**Projeto:** Arquitetura Multi-Tenant para Gestão de Propriedades Rurais
**Data da execução:** 05 de julho de 2026
**Ambiente:** macOS 24.4.0 · Python 3.13.2 · Django 6.0.3 · PostgreSQL 15.17 (dev local) · Coverage 7.14+

---

## 1. Comandos executados

```bash
DB_NAME=agrodb DB_USER=postgres DB_PASSWORD=postgres123 \
DB_HOST=localhost DB_PORT=5432 \
.venv/bin/python -m coverage run --source=api,customers,config manage.py test

.venv/bin/python -m coverage report --skip-empty
```

## 2. Resumo agregado

| Métrica | Resultado |
|---|---|
| Testes executados | **25** |
| Falhas | 0 |
| Erros | 0 |
| Tempo total | **13,887 s** |
| Cobertura global | **73 %** |

Saída resumida do test runner:

```
Ran 25 tests in 13.887s

OK
Destroying test database for alias 'default'...
```

## 3. Cobertura dos principais arquivos da API

| Arquivo | Cobertura |
|---|---|
| `api/models.py` | **96 %** |
| `api/views.py` | **100 %** |
| `api/serializers.py` | **100 %** |
| `api/urls.py` | **100 %** |
| `api/forms_web.py` | **100 %** |
| `api/tests.py` | 98 % |
| `api/alertas_service.py` | 82 % |
| `api/views_web.py` | 64 % |
| `api/context_processors.py` | 69 % |
| `api/forms.py` | 53 % |
| `api/views_auth.py` | 24 % (fluxos web auxiliares) |
| `customers/models.py` | **94 %** |
| `customers/admin.py` | 77 % |
| `customers/middleware.py` | 65 % |
| `config/settings.py` | 100 % |
| `config/views_health.py` | 100 % |
| `config/urls_tenant.py` | 100 % |

Arquivos com 0 % (`wsgi.py`, `asgi.py`, `urls_public.py`, `tenant_http.py`,
`views_metrics.py`, `views_public.py`, `ensure_postgres_database`) são
entrypoints ou comandos de infraestrutura sem cobertura direta pelos casos
de teste — comportamento esperado.

Cobertura total (linhas):

```
TOTAL   1396 stmts   377 miss   73 %
```

## 4. Detalhamento dos 25 casos de teste

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

## 5. Interpretação

A execução confirma:

- **Isolamento multi-tenant** validado (`IsolamentoEntreTenantsTest` cria dois
  tenants distintos e demonstra que dados de um não vazam para o outro).
- **Autenticação JWT** validada de ponta a ponta (emissão, recusa de credencial
  inválida e bloqueio de acesso anônimo).
- **API REST** exercitada com listagem, criação e busca autenticadas.
- **Relatórios CSV e PDF** validados por bytes (BOM UTF-8, cabeçalho `%PDF`) e
  também com carga maior (30 propriedades, 12 compras/vendas por propriedade)
  para garantir robustez do fluxo consolidado.
- **Health check** validado nos contextos público e de tenant, cobrindo o
  endpoint usado pelas probes do Kubernetes.
- **Cobertura de 73 %** com 100 % nos módulos centrais (`views`, `serializers`,
  `urls`, `forms_web`) e ≥94 % nos modelos (`api/models.py`, `customers/models.py`),
  o que endereça diretamente o requisito de testabilidade (RA6) e a preocupação
  levantada pela banca sobre a solidez da avaliação.
