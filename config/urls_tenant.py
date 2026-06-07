"""
URLs usadas quando a requisição é para um domínio de inquilino (tenant).
Páginas web (login/registro) + API REST em /api/.
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from api.views_auth import dashboard_view, register_view
from .views_health import healthz_view

urlpatterns = [
    path("healthz/", healthz_view, name="healthz_tenant"),
    path("", dashboard_view, name="tenant_home"),
    path("", include("api.urls_web")),
    path("registrar/", register_view, name="register"),
    path(
        "login/",
        LoginView.as_view(
            template_name="api/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(next_page="/login/"),
        name="logout",
    ),
    path("api/", include("api.urls")),
]
