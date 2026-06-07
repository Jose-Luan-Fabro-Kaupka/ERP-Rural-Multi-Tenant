from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django_tenants.utils import get_public_schema_name, schema_context

from customers.models import GlobalConfig

from .alertas_service import sincronizar_alertas_financeiros
from .forms import TenantUserCreationForm
from .models import (
    AplicacaoInsumo,
    Compra,
    Insumo,
    Plantacao,
    Produto,
    Propriedade,
    Venda,
)

User = get_user_model()


def _safe_redirect_url(request, url):
    if not url:
        return None
    if url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return None


def _user_can(user, perm):
    return user.is_superuser or user.has_perm(perm)


@login_required
def dashboard_view(request):
    u = request.user
    if _user_can(u, "api.view_propriedade") or _user_can(u, "api.view_alerta"):
        sincronizar_alertas_financeiros()

    ctx = {}
    if _user_can(u, "api.view_propriedade"):
        ctx["n_propriedades"] = Propriedade.objects.count()
    if _user_can(u, "api.view_produto"):
        ctx["n_produtos"] = Produto.objects.count()
    if _user_can(u, "api.view_insumo"):
        ctx["n_insumos"] = Insumo.objects.count()
    if _user_can(u, "api.view_plantacao"):
        ctx["n_plantacoes"] = Plantacao.objects.count()
    if _user_can(u, "api.view_compra"):
        ctx["n_compras"] = Compra.objects.count()
    if _user_can(u, "api.view_venda"):
        ctx["n_vendas"] = Venda.objects.count()
    if _user_can(u, "api.view_aplicacaoinsumo"):
        ctx["n_aplicacoes"] = AplicacaoInsumo.objects.count()

    return render(request, "api/dashboard.html", ctx)


def register_view(request):
    with schema_context(get_public_schema_name()):
        cfg = GlobalConfig.get_solo()

    ctx = {
        "form": None,
        "next": request.POST.get("next") or request.GET.get("next") or "",
        "registration_disabled": not cfg.allow_new_user_registration,
        "registration_limit": False,
    }

    if request.user.is_authenticated:
        return redirect("tenant_home")

    if ctx["registration_disabled"]:
        ctx["form"] = TenantUserCreationForm()
        return render(request, "api/register.html", ctx)

    if (
        cfg.max_users_per_tenant is not None
        and User.objects.count() >= cfg.max_users_per_tenant
    ):
        ctx["registration_limit"] = True
        ctx["form"] = TenantUserCreationForm()
        return render(request, "api/register.html", ctx)

    if request.method == "POST":
        form = TenantUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            target = _safe_redirect_url(request, ctx["next"])
            return redirect(target or "tenant_home")
    else:
        form = TenantUserCreationForm()
    ctx["form"] = form
    return render(request, "api/register.html", ctx)
