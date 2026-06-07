# customers/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Modelo que representa um inquilino (fazenda / propriedade)
    usado pelo django-tenants (no schema public).
    """
    name = models.CharField(max_length=200)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)

    # opções do TenantMixin: domain_url, schema_name, etc são geradas
    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    class Meta:
        verbose_name = "Inquilino (fazenda)"
        verbose_name_plural = "Inquilinos (fazendas)"


class Domain(DomainMixin):
    """
    Domínios/subdomínios associados ao tenant (também no public).
    """

    class Meta:
        verbose_name = "Domínio"
        verbose_name_plural = "Domínios"


class GlobalConfig(models.Model):
    """
    Configuração única da plataforma (schema public).
    Limites globais, manutenção e políticas de cadastro.
    """

    max_tenants = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Máximo de inquilinos (vazio = sem limite).",
    )
    max_users_per_tenant = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Máximo de usuários por schema de tenant (vazio = sem limite).",
    )
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Se ativo, usuários não-staff recebem 503 nas rotas de tenant.",
    )
    maintenance_message = models.TextField(
        blank=True,
        default="Plataforma em manutenção. Tente novamente em instantes.",
    )
    allow_new_user_registration = models.BooleanField(
        default=True,
        help_text="Permite auto-registro em /registrar/ nos domínios de tenant.",
    )

    class Meta:
        verbose_name = "Configuração global"
        verbose_name_plural = "Configuração global"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
