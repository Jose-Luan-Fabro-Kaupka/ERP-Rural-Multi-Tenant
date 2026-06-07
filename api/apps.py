from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "Gestão rural (tenant)"

    def ready(self):
        from django_tenants.models import TenantMixin
        from django_tenants.signals import post_schema_sync

        from .signals import bootstrap_tenant_roles

        post_schema_sync.connect(
            bootstrap_tenant_roles,
            sender=TenantMixin,
            dispatch_uid="api_bootstrap_tenant_roles",
        )
