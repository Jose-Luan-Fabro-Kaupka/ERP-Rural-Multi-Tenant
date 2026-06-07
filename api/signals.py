from io import StringIO

from django.core.management import call_command


def bootstrap_tenant_roles(sender, tenant, **kwargs):
    """Após sync do schema do tenant, cria grupos e permissões padrão."""
    from django_tenants.utils import tenant_context

    with tenant_context(tenant):
        call_command("setup_tenant_roles", stdout=StringIO())
