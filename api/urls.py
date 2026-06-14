# api/urls.py
# Direcionamento dos endpoints
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    PropriedadeViewSet,
    ProdutoViewSet,
    InsumoViewSet,
    PlantacaoViewSet,
    CompraViewSet,
    VendaViewSet,
    AplicacaoInsumoViewSet,
    AlertaViewSet,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'propriedades', PropriedadeViewSet)
router.register(r'produtos', ProdutoViewSet)
router.register(r'insumos', InsumoViewSet)
router.register(r'plantacoes', PlantacaoViewSet)
router.register(r'compras', CompraViewSet)
router.register(r'vendas', VendaViewSet)
router.register(r'aplicacoes', AplicacaoInsumoViewSet)
router.register(r'alertas', AlertaViewSet)

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
