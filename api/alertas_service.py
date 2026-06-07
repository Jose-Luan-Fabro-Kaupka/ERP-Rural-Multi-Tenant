"""
Geração de alertas de negócio.
"""
from decimal import Decimal

from django.utils import timezone

from .models import Alerta, Compra, Propriedade, Venda


def sincronizar_alertas_financeiros():
    """
    Cria ou remove alertas quando há desequilíbrio entre compras e vendas.
    """
    total_c = sum((x.total() for x in Compra.objects.all()), Decimal("0"))
    total_v = sum((x.total() for x in Venda.objects.all()), Decimal("0"))
    hoje = timezone.now().date().isoformat()
    codigo = f"fin_balanco_{hoje}"

    if total_c > 0 and total_v > 0:
        if total_c > total_v * Decimal("2"):
            Alerta.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "titulo": "Compras muito acima das vendas",
                    "mensagem": (
                        f"Total de compras ({total_c}) é mais que o dobro das vendas ({total_v})."
                    ),
                    "severidade": Alerta.Severidade.CRITICO,
                    "lido": False,
                },
            )
        elif total_c > total_v * Decimal("1.2"):
            Alerta.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "titulo": "Compras superam vendas",
                    "mensagem": (
                        f"Compras ({total_c}) estão mais de 20% acima das vendas ({total_v})."
                    ),
                    "severidade": Alerta.Severidade.AVISO,
                    "lido": False,
                },
            )
        else:
            Alerta.objects.filter(codigo=codigo).delete()
    else:
        Alerta.objects.filter(codigo=codigo).delete()

    for prop in Propriedade.objects.all():
        tc = sum((x.total() for x in Venda.objects.filter(propriedade=prop)), Decimal("0"))
        cc = sum((x.total() for x in Compra.objects.filter(propriedade=prop)), Decimal("0"))
        c2 = f"fin_prop_{prop.pk}_{hoje}"
        if tc > 0 and cc > tc * Decimal("2"):
            Alerta.objects.update_or_create(
                codigo=c2,
                defaults={
                    "titulo": f"Propriedade {prop.nome}: compras elevadas",
                    "mensagem": (
                        f"Compras ({cc}) são mais que o dobro das vendas ({tc}) nesta propriedade."
                    ),
                    "severidade": Alerta.Severidade.AVISO,
                    "propriedade": prop,
                    "lido": False,
                },
            )
        else:
            Alerta.objects.filter(codigo=c2).delete()
