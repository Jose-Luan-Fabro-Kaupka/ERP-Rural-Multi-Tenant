# api/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

from .models import (
    Propriedade,
    Produto,
    Insumo,
    Plantacao,
    Compra,
    Venda,
    AplicacaoInsumo,
    Alerta,
)
from .serializers import (
    PropriedadeSerializer,
    ProdutoSerializer,
    InsumoSerializer,
    PlantacaoSerializer,
    CompraSerializer,
    VendaSerializer,
    AplicacaoInsumoSerializer,
    AlertaSerializer,
)


class BaseTenantModelViewSet(viewsets.ModelViewSet):
    """
    Exige autenticação e permissões Django por modelo (RBAC por tenant).
    GET → view_*, POST → add_*, PATCH/PUT → change_*, DELETE → delete_*.
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = []
    ordering_fields = "__all__"
    ordering = ["id"]


class PropriedadeViewSet(BaseTenantModelViewSet):
    queryset = Propriedade.objects.all()
    serializer_class = PropriedadeSerializer
    search_fields = ["nome", "codigo", "localizacao"]


class ProdutoViewSet(BaseTenantModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    search_fields = ["nome", "descricao", "unidade"]


class InsumoViewSet(BaseTenantModelViewSet):
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer
    search_fields = ["nome", "tipo", "medida_unidade"]


class PlantacaoViewSet(BaseTenantModelViewSet):
    queryset = Plantacao.objects.select_related("propriedade", "produto").all()
    serializer_class = PlantacaoSerializer
    search_fields = ["talhao", "propriedade__nome", "produto__nome"]


class CompraViewSet(BaseTenantModelViewSet):
    queryset = Compra.objects.select_related("propriedade", "insumo").all()
    serializer_class = CompraSerializer
    search_fields = ["propriedade__nome", "insumo__nome"]


class VendaViewSet(BaseTenantModelViewSet):
    queryset = Venda.objects.select_related("propriedade", "produto").all()
    serializer_class = VendaSerializer
    search_fields = ["propriedade__nome", "produto__nome"]


class AplicacaoInsumoViewSet(BaseTenantModelViewSet):
    queryset = AplicacaoInsumo.objects.select_related("plantacao", "insumo").all()
    serializer_class = AplicacaoInsumoSerializer
    search_fields = [
        "insumo__nome",
        "plantacao__talhao",
        "plantacao__propriedade__nome",
        "plantacao__produto__nome",
    ]


class AlertaViewSet(viewsets.ReadOnlyModelViewSet):
    """Alertas gerados pelo sistema: leitura via API; marcar lido no portal web."""

    queryset = Alerta.objects.select_related("propriedade").all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "severidade"]
    ordering = ["-created_at"]
