"""
URLs usadas no schema público (domínio principal).
Portal de entrada por fazenda, admin e criação/gestão de inquilinos.
"""
from django.contrib import admin
from django.urls import path

from customers.views_public import entrar_fazenda_view
from customers.views_metrics import platform_metrics_view
from .views_health import healthz_view

urlpatterns = [
    path("healthz/", healthz_view, name="healthz"),
    path("", entrar_fazenda_view, name="public_portal"),
    path("entrar/", entrar_fazenda_view, name="entrar_fazenda"),
    path("metricas/", platform_metrics_view, name="platform_metrics"),
    path("admin/", admin.site.urls),
]
