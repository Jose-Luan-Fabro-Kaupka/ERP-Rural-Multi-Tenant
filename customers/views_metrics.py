"""
Métricas agregadas da plataforma (schema public) — staff Django.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils import timezone

from .models import Client, Domain, GlobalConfig


@staff_member_required
def platform_metrics_view(request):
    n_clients = Client.objects.count()
    n_domains = Domain.objects.count()
    cfg = GlobalConfig.get_solo()
    rows = "".join(
        f"<tr><td>{c.schema_name}</td><td>{c.name}</td><td>{c.created_on}</td></tr>"
        for c in Client.objects.order_by("-created_on")[:50]
    )
    html = f"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="utf-8"><title>Métricas — Agro SaaS</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #0f1419; color: #e7edf4; }}
table {{ border-collapse: collapse; width: 100%; max-width: 720px; }}
th, td {{ border: 1px solid #2a3544; padding: 0.5rem 0.75rem; text-align: left; }}
th {{ background: #1a222c; }}
a {{ color: #3d9e6f; }}
.box {{ background: #1a222c; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; max-width: 720px; }}
</style></head><body>
<p><a href="/admin/">← Admin</a></p>
<h1>Utilização da plataforma</h1>
<p class="box">Gerado em {timezone.now().isoformat()} — visão do schema <strong>public</strong>.</p>
<div class="box">
<p><strong>Inquilinos (Client):</strong> {n_clients}</p>
<p><strong>Domínios:</strong> {n_domains}</p>
<p><strong>Manutenção:</strong> {"sim" if cfg.maintenance_mode else "não"}</p>
<p><strong>Limite de inquilinos:</strong> {cfg.max_tenants if cfg.max_tenants is not None else "—"}</p>
<p><strong>Limite usuários/tenant:</strong> {cfg.max_users_per_tenant if cfg.max_users_per_tenant is not None else "—"}</p>
<p><strong>Auto-registro em tenants:</strong> {"sim" if cfg.allow_new_user_registration else "não"}</p>
</div>
<h2>Inquilinos recentes</h2>
<table><thead><tr><th>Schema</th><th>Nome</th><th>Criado em</th></tr></thead>
<tbody>{rows or "<tr><td colspan='3'>Nenhum</td></tr>"}</tbody></table>
</body></html>"""
    return HttpResponse(html)
