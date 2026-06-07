# api/serializers.py
from rest_framework import serializers
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

class PropriedadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propriedade
        fields = '__all__'

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'

class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        fields = '__all__'

class PlantacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plantacao
        fields = '__all__'

class CompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compra
        fields = '__all__'

class VendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venda
        fields = '__all__'

class AplicacaoInsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AplicacaoInsumo
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = "__all__"
