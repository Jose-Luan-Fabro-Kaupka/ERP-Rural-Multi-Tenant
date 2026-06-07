# api/models.py
from django.db import models
from django.core.validators import MinValueValidator

class Propriedade(models.Model):
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    localizacao = models.CharField(max_length=255, blank=True, null=True)
    area_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    unidade = models.CharField(max_length=20, default="kg")  # ex: kg, t, un
    preco_padrao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nome

class Insumo(models.Model):
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=100, blank=True, null=True)
    medida_unidade = models.CharField(max_length=20, default="kg")

    def __str__(self):
        return self.nome

class Plantacao(models.Model):
    propriedade = models.ForeignKey(Propriedade, related_name="plantacoes", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    talhao = models.CharField(max_length=100, blank=True, null=True)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    rendimento_estimado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.produto.nome} - {self.propriedade.nome} ({self.talhao})"

class Compra(models.Model):
    propriedade = models.ForeignKey(Propriedade, related_name="compras", on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    unidade = models.CharField(max_length=20)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    data_compra = models.DateField()

    def total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"Compra {self.insumo.nome} - {self.propriedade.nome} - {self.data_compra}"

class Venda(models.Model):
    propriedade = models.ForeignKey(Propriedade, related_name="vendas", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    unidade = models.CharField(max_length=20)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    data_venda = models.DateField()

    def total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"Venda {self.produto.nome} - {self.propriedade.nome} - {self.data_venda}"

class AplicacaoInsumo(models.Model):
    plantacao = models.ForeignKey(Plantacao, related_name="aplicacoes", on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    data_aplicacao = models.DateField()
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.insumo.nome} @ {self.plantacao}"


class Alerta(models.Model):
    """Alertas de negócio exibidos no portal."""

    class Severidade(models.TextChoices):
        INFO = "info", "Informação"
        AVISO = "aviso", "Aviso"
        CRITICO = "critico", "Crítico"

    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    severidade = models.CharField(
        max_length=10,
        choices=Severidade.choices,
        default=Severidade.AVISO,
    )
    codigo = models.CharField(
        max_length=120,
        db_index=True,
        blank=True,
        help_text="Chave lógica para evitar duplicatas (ex.: regra financeira diária).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    lido = models.BooleanField(default=False)
    propriedade = models.ForeignKey(
        Propriedade,
        null=True,
        blank=True,
        related_name="alertas",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"

    def __str__(self):
        return self.titulo
