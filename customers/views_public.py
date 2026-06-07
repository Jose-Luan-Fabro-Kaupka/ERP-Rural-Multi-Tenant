"""
Páginas no schema público (host sem tenant): portal para escolher fazenda e ir ao login do tenant.
"""
from django.conf import settings
from django.shortcuts import redirect, render

from .models import Client, Domain


def _resolve_domain(identifier: str):
    raw = (identifier or "").strip()
    if not raw:
        return None
    key = raw.lower()

    d = Domain.objects.filter(domain__iexact=key).first()
    if d:
        return d

    if "." not in key:
        base = getattr(settings, "TENANT_SUBDOMAIN_BASE", "localhost")
        d = Domain.objects.filter(domain__iexact=f"{key}.{base}").first()
        if d:
            return d

    client = Client.objects.filter(schema_name__iexact=key).first()
    if client:
        return client.domains.filter(is_primary=True).first() or client.domains.first()
    return None


def _tenant_login_url(request, domain_host: str) -> str:
    """
    Monta a URL de login do tenant. Hosts sem ponto (ex.: fazenda1) não resolvem no DNS;
    em dev usa-se fazenda1.<TENANT_SUBDOMAIN_BASE> (ex.: fazenda1.localhost → 127.0.0.1).
    """
    base = getattr(settings, "TENANT_SUBDOMAIN_BASE", "localhost")
    host = (domain_host or "").strip()
    if host and "." not in host:
        host = f"{host}.{base}"

    port = request.get_port()
    default = ("443" if request.scheme == "https" else "80")
    if str(port) == default:
        netloc = host
    else:
        netloc = f"{host}:{port}"
    return f"{request.scheme}://{netloc}/login/"


def entrar_fazenda_view(request):
    error = None
    fazenda = ""

    if request.method == "POST":
        fazenda = request.POST.get("fazenda", "")
    elif request.method == "GET":
        fazenda = request.GET.get("fazenda", "")

    if fazenda:
        domain = _resolve_domain(fazenda)
        if domain:
            return redirect(_tenant_login_url(request, domain.domain))
        error = (
            "Fazenda não encontrada. Use o nome do schema, o subdomínio ou o domínio "
            "cadastrado no admin (ex.: fazenda1 ou fazenda1.localhost)."
        )

    return render(
        request,
        "public/entrar_fazenda.html",
        {"error": error, "fazenda": fazenda},
    )
