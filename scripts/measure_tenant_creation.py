#!/usr/bin/env python
"""
Mede o tempo necessário para criar um novo tenant no modelo schema-per-tenant.

Cada execução:

1. Cria uma instância de ``Client`` no schema público.
2. Registra um ``Domain`` primário.
3. Aplica ``migrate_schemas`` no schema recém-criado (o custo real do modelo).

O tempo total (criação + domínio + migrações do schema) é medido com
``time.perf_counter`` e reportado por execução. Ao final é gerada uma tabela
com média, mediana, mínimo e máximo. Também é possível salvar o resultado em
Markdown para uso direto no relatório do TCC.

Uso típico (execução local):

    DB_NAME=agrodb DB_USER=postgres DB_PASSWORD=postgres123 \
    DB_HOST=localhost DB_PORT=5432 \
    .venv/bin/python scripts/measure_tenant_creation.py --runs 5 \
        --output docs/resultados-criacao-tenant.md

Uso dentro do container Docker:

    docker exec -it agro_api python scripts/measure_tenant_creation.py --runs 5

Os tenants criados durante a medição são removidos ao final para não
poluir o banco (schemas são dropados via ``migrate_schemas``/DROP SCHEMA).
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
import uuid
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django_tenants.utils import get_tenant_model  # noqa: E402

from customers.models import Domain  # noqa: E402


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def create_tenant_measured(schema_name: str, domain: str) -> float:
    """Executa a criação completa de um tenant e devolve o tempo em segundos."""
    Tenant = get_tenant_model()
    t0 = time.perf_counter()
    tenant = Tenant(schema_name=schema_name, name=f"Tenant Bench {schema_name}")
    tenant.save()
    Domain.objects.create(domain=domain, tenant=tenant, is_primary=True)
    call_command(
        "migrate_schemas",
        schema_name=schema_name,
        verbosity=0,
        interactive=False,
    )
    return time.perf_counter() - t0


def drop_schema(schema_name: str) -> None:
    """Remove o schema criado durante o benchmark."""
    Tenant = get_tenant_model()
    try:
        tenant = Tenant.objects.get(schema_name=schema_name)
    except Tenant.DoesNotExist:
        return
    Domain.objects.filter(tenant=tenant).delete()
    with connection.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
    tenant.delete()


def format_markdown(times: list[float]) -> str:
    lines = [
        "# Resultados — Tempo de criação de tenant",
        "",
        "Métrica de multi-tenancy (modelo schema-per-tenant).",
        "",
        "Cada execução inclui: `INSERT` do tenant no schema público, `INSERT`",
        "do domínio primário e `migrate_schemas` do schema recém-criado.",
        "",
        "| Execução | Tempo de criação do tenant (s) |",
        "|---:|---:|",
    ]
    for i, seconds in enumerate(times, start=1):
        lines.append(f"| {i} | {seconds:.3f} |")
    media = statistics.mean(times)
    mediana = statistics.median(times)
    minimo = min(times)
    maximo = max(times)
    lines.append(f"| **Média** | **{media:.3f}** |")
    lines.append(f"| Mediana | {mediana:.3f} |")
    lines.append(f"| Mínimo | {minimo:.3f} |")
    lines.append(f"| Máximo | {maximo:.3f} |")
    lines.append("")
    lines.append(
        "> Medido com `time.perf_counter` em ambiente de desenvolvimento local. "
        "O custo dominante é o `migrate_schemas`, que aplica as migrações da "
        "aplicação de negócio (`api`) no schema recém-criado."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5, help="Quantidade de execuções (default 5)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Caminho para salvar o relatório em Markdown (opcional)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Se definido, não remove os tenants criados ao final.",
    )
    args = parser.parse_args()

    call_command("migrate_schemas", "--shared", verbosity=0, interactive=False)

    times: list[float] = []
    created: list[str] = []
    try:
        for i in range(1, args.runs + 1):
            schema = f"bench_{_unique_suffix()}"
            domain = f"{schema}.localhost"
            elapsed = create_tenant_measured(schema, domain)
            created.append(schema)
            times.append(elapsed)
            print(f"[{i}/{args.runs}] schema={schema} tempo={elapsed:.3f}s")
    finally:
        if not args.keep:
            for schema in created:
                drop_schema(schema)

    if not times:
        print("Nenhuma execução realizada.", file=sys.stderr)
        return 1

    print("\nResumo:")
    print(f"  execuções: {len(times)}")
    print(f"  média:   {statistics.mean(times):.3f}s")
    print(f"  mediana: {statistics.median(times):.3f}s")
    print(f"  mínimo:  {min(times):.3f}s")
    print(f"  máximo:  {max(times):.3f}s")

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(format_markdown(times), encoding="utf-8")
        print(f"\nRelatório salvo em: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
