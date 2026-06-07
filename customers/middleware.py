from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django_tenants.middleware.main import TenantMainMiddleware as _BaseTenantMainMiddleware
from django_tenants.utils import get_public_schema_name, schema_context

from customers.models import GlobalConfig


class TenantMainMiddleware(_BaseTenantMainMiddleware):
    """
    Além do host exato em Domain, aceita fazenda1.localhost quando o cadastro é só fazenda1
    (evita DNS_PROBE em navegadores que não resolvem hostnames de uma etiqueta).

    Sem isso, o django-tenants cai em SHOW_PUBLIC_IF_NO_TENANT_FOUND e o urlconf público
    não tem /login/, gerando 404.
    """

    def get_tenant(self, domain_model, hostname):
        base = (getattr(settings, "TENANT_SUBDOMAIN_BASE", "localhost") or "localhost").strip()

        domain = (
            domain_model.objects.select_related("tenant")
            .filter(domain__iexact=hostname)
            .first()
        )
        if domain:
            return domain.tenant

        suffix = f".{base.lower()}"
        if hostname.lower().endswith(suffix):
            prefix = hostname[: len(hostname) - len(suffix)]
            if prefix and "." not in prefix:
                domain = (
                    domain_model.objects.select_related("tenant")
                    .filter(domain__iexact=prefix)
                    .first()
                )
                if domain:
                    return domain.tenant

        raise domain_model.DoesNotExist

    @staticmethod
    def setup_url_routing(request, force_public=False):
        _BaseTenantMainMiddleware.setup_url_routing(request, force_public=force_public)
        if force_public:
            return
        tenant = getattr(request, "tenant", None)
        public = get_public_schema_name()
        if tenant is not None and getattr(tenant, "schema_name", None) != public:
            request.urlconf = settings.ROOT_URLCONF


class MaintenanceModeMiddleware:
    """
    No schema de tenant: se maintenance_mode estiver ativo na GlobalConfig (public),
    bloqueia rotas exceto login/logout/registrar e usuários staff do tenant.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(connection, "tenant", None)
        public = get_public_schema_name()
        if tenant is None or getattr(tenant, "schema_name", None) == public:
            return self.get_response(request)

        with schema_context(public):
            cfg = GlobalConfig.get_solo()
        if not cfg.maintenance_mode:
            return self.get_response(request)

        path = request.path
        if (
            path.startswith("/login")
            or path.startswith("/logout")
            or path.startswith("/registrar")
        ):
            return self.get_response(request)

        u = request.user
        if u.is_authenticated and u.is_staff:
            return self.get_response(request)

        return HttpResponse(
            "<html><body style='font-family:sans-serif;padding:2rem;'>"
            f"<h1>Manutenção</h1><p>{cfg.maintenance_message}</p></body></html>",
            status=503,
            content_type="text/html; charset=utf-8",
        )
