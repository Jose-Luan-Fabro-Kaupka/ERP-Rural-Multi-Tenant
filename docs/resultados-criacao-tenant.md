# Resultados — Tempo de criação de tenant

Métrica de multi-tenancy (modelo schema-per-tenant).

Cada execução inclui: `INSERT` do tenant no schema público, `INSERT`
do domínio primário e `migrate_schemas` do schema recém-criado.

| Execução | Tempo de criação do tenant (s) |
|---:|---:|
| 1 | 0.272 |
| 2 | 0.332 |
| 3 | 0.315 |
| 4 | 0.245 |
| 5 | 0.241 |
| **Média** | **0.281** |
| Mediana | 0.272 |
| Mínimo | 0.241 |
| Máximo | 0.332 |

> Medido com `time.perf_counter` em ambiente de desenvolvimento local. O custo dominante é o `migrate_schemas`, que aplica as migrações da aplicação de negócio (`api`) no schema recém-criado.
