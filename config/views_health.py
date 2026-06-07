"""Endpoints mínimos para probes (Kubernetes) e monitoramento."""

from django.http import HttpResponse


def healthz_view(request):
    """Resposta leve; não toca no banco. Usar com Host permitido em ALLOWED_HOSTS."""
    return HttpResponse("OK\n", content_type="text/plain; charset=utf-8")
