from django import forms

from .models import (
    AplicacaoInsumo,
    Compra,
    Insumo,
    Plantacao,
    Produto,
    Propriedade,
    Venda,
)

_field = {"class": "field-input"}


class PropriedadeForm(forms.ModelForm):
    class Meta:
        model = Propriedade
        fields = "__all__"
        widgets = {
            "nome": forms.TextInput(attrs=_field),
            "codigo": forms.TextInput(attrs=_field),
            "localizacao": forms.TextInput(attrs=_field),
            "area_total": forms.NumberInput(attrs={**_field, "step": "any"}),
            "observacoes": forms.Textarea(attrs={**_field, "rows": 4}),
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = "__all__"
        widgets = {
            "nome": forms.TextInput(attrs=_field),
            "descricao": forms.Textarea(attrs={**_field, "rows": 3}),
            "unidade": forms.TextInput(attrs=_field),
            "preco_padrao": forms.NumberInput(attrs={**_field, "step": "any"}),
        }


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = "__all__"
        widgets = {
            "nome": forms.TextInput(attrs=_field),
            "tipo": forms.TextInput(attrs=_field),
            "medida_unidade": forms.TextInput(attrs=_field),
        }


class PlantacaoForm(forms.ModelForm):
    class Meta:
        model = Plantacao
        fields = "__all__"
        widgets = {
            "propriedade": forms.Select(attrs=_field),
            "produto": forms.Select(attrs=_field),
            "talhao": forms.TextInput(attrs=_field),
            "area": forms.NumberInput(attrs={**_field, "step": "any"}),
            "data_inicio": forms.DateInput(attrs={**_field, "type": "date"}),
            "data_fim": forms.DateInput(attrs={**_field, "type": "date"}),
            "rendimento_estimado": forms.NumberInput(attrs={**_field, "step": "any"}),
        }


class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = "__all__"
        widgets = {
            "propriedade": forms.Select(attrs=_field),
            "insumo": forms.Select(attrs=_field),
            "quantidade": forms.NumberInput(attrs={**_field, "step": "any"}),
            "unidade": forms.TextInput(attrs=_field),
            "preco_unitario": forms.NumberInput(attrs={**_field, "step": "any"}),
            "data_compra": forms.DateInput(attrs={**_field, "type": "date"}),
        }


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = "__all__"
        widgets = {
            "propriedade": forms.Select(attrs=_field),
            "produto": forms.Select(attrs=_field),
            "quantidade": forms.NumberInput(attrs={**_field, "step": "any"}),
            "unidade": forms.TextInput(attrs=_field),
            "preco_unitario": forms.NumberInput(attrs={**_field, "step": "any"}),
            "data_venda": forms.DateInput(attrs={**_field, "type": "date"}),
        }


class AplicacaoInsumoForm(forms.ModelForm):
    class Meta:
        model = AplicacaoInsumo
        fields = "__all__"
        widgets = {
            "plantacao": forms.Select(attrs=_field),
            "insumo": forms.Select(attrs=_field),
            "quantidade": forms.NumberInput(attrs={**_field, "step": "any"}),
            "data_aplicacao": forms.DateInput(attrs={**_field, "type": "date"}),
            "observacoes": forms.Textarea(attrs={**_field, "rows": 3}),
        }
