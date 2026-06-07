from django.db import connection
from django_tenants.utils import get_public_schema_name


def nav_alertas(request):
    if not request.user.is_authenticated:
        return {}
    tenant = getattr(connection, "tenant", None)
    if tenant is None or getattr(tenant, "schema_name", None) == get_public_schema_name():
        return {}
    try:
        from .models import Alerta

        return {"nav_alertas_nao_lidos": Alerta.objects.filter(lido=False).count()}
    except Exception:
        return {}
