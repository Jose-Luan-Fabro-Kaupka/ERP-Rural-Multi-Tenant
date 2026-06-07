"""
Admin para gestão de inquilinos (Client e Domain).
Acesso apenas no schema público (domínio principal). Permite cadastrar
novas propriedades/tenants e seus domínios de acesso.
"""
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from config.admin_forms import BootstrapAdminAuthenticationForm

from .models import Client, Domain, GlobalConfig

admin.site.login_form = BootstrapAdminAuthenticationForm
admin.site.site_header = "Agro SaaS"
admin.site.site_title = "Agro SaaS"
admin.site.index_title = "Área administrativa"


class DomainInline(admin.TabularInline):
    """Permite cadastrar o hostname do tenant ao criar ou editar a fazenda."""

    model = Domain
    extra = 1
    fields = ("domain", "is_primary")
    verbose_name = "Domínio"
    verbose_name_plural = "Domínios de acesso"


@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    list_display = [
        "max_tenants",
        "max_users_per_tenant",
        "maintenance_mode",
        "allow_new_user_registration",
    ]

    def has_add_permission(self, request):
        if GlobalConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    inlines = [DomainInline]
    list_display = ["name", "schema_name", "created_on", "on_trial", "paid_until"]
    list_filter = ["on_trial", "created_on"]
    search_fields = ["name", "schema_name"]
    ordering = ["-created_on"]
    fieldsets = (
        (None, {"fields": ("schema_name", "name")}),
        ("Contrato", {"fields": ("on_trial", "paid_until")}),
    )

    def has_add_permission(self, request):
        if not super().has_add_permission(request):
            return False
        cfg = GlobalConfig.get_solo()
        if cfg.max_tenants is None:
            return True
        return Client.objects.count() < cfg.max_tenants


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
    list_filter = ["is_primary"]
    search_fields = ["domain"]
    raw_id_fields = ["tenant"]
