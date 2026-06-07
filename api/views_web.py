import csv
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms_web import (
    AplicacaoInsumoForm,
    CompraForm,
    InsumoForm,
    PlantacaoForm,
    ProdutoForm,
    PropriedadeForm,
    VendaForm,
)
from .models import (
    AplicacaoInsumo,
    Alerta,
    Compra,
    Insumo,
    Plantacao,
    Produto,
    Propriedade,
    Venda,
)
from .alertas_service import sincronizar_alertas_financeiros


class PortalAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = "/login/"
    raise_exception = True


class PropriedadeFilteredMixin:
    """Filtra por ?propriedade=<pk> quando o modelo tem FK propriedade."""

    fk_name = "propriedade"

    def get_queryset(self):
        qs = super().get_queryset()
        pid = self.request.GET.get("propriedade")
        if pid:
            try:
                qs = qs.filter(**{self.fk_name: int(pid)})
            except (TypeError, ValueError):
                pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pid = self.request.GET.get("propriedade")
        ctx["filter_propriedade_id"] = pid
        if pid:
            try:
                ctx["filter_propriedade"] = Propriedade.objects.filter(pk=int(pid)).first()
            except (TypeError, ValueError):
                pass
        return ctx


# --- Propriedade ---
class PropriedadeListView(PortalAccessMixin, ListView):
    permission_required = ("api.view_propriedade",)
    model = Propriedade
    template_name = "api/portal/propriedade_list.html"
    context_object_name = "object_list"


class PropriedadeCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_propriedade",)
    model = Propriedade
    form_class = PropriedadeForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Nova propriedade"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("propriedade_list")
        return ctx

    def get_success_url(self):
        return reverse("propriedade_list")


class PropriedadeUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_propriedade",)
    model = Propriedade
    form_class = PropriedadeForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar propriedade"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("propriedade_list")
        return ctx

    def get_success_url(self):
        return reverse("propriedade_list")


class PropriedadeDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_propriedade",)
    model = Propriedade
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("propriedade_list")
        return ctx

    def get_success_url(self):
        return reverse("propriedade_list")


# --- Produto ---
class ProdutoListView(PortalAccessMixin, ListView):
    permission_required = ("api.view_produto",)
    model = Produto
    template_name = "api/portal/produto_list.html"
    context_object_name = "object_list"


class ProdutoCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_produto",)
    model = Produto
    form_class = ProdutoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Novo produto"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("produto_list")
        return ctx

    def get_success_url(self):
        return reverse("produto_list")


class ProdutoUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_produto",)
    model = Produto
    form_class = ProdutoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar produto"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("produto_list")
        return ctx

    def get_success_url(self):
        return reverse("produto_list")


class ProdutoDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_produto",)
    model = Produto
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("produto_list")
        return ctx

    def get_success_url(self):
        return reverse("produto_list")


# --- Insumo ---
class InsumoListView(PortalAccessMixin, ListView):
    permission_required = ("api.view_insumo",)
    model = Insumo
    template_name = "api/portal/insumo_list.html"
    context_object_name = "object_list"


class InsumoCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_insumo",)
    model = Insumo
    form_class = InsumoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Novo insumo"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("insumo_list")
        return ctx

    def get_success_url(self):
        return reverse("insumo_list")


class InsumoUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_insumo",)
    model = Insumo
    form_class = InsumoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar insumo"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("insumo_list")
        return ctx

    def get_success_url(self):
        return reverse("insumo_list")


class InsumoDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_insumo",)
    model = Insumo
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("insumo_list")
        return ctx

    def get_success_url(self):
        return reverse("insumo_list")


# --- Plantação ---
class PlantacaoListView(PortalAccessMixin, PropriedadeFilteredMixin, ListView):
    permission_required = ("api.view_plantacao",)
    model = Plantacao
    template_name = "api/portal/plantacao_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("propriedade", "produto")
        )


class PlantacaoCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_plantacao",)
    model = Plantacao
    form_class = PlantacaoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Nova plantação"}

    def get_initial(self):
        initial = super().get_initial()
        pid = self.request.GET.get("propriedade")
        if pid:
            try:
                initial["propriedade"] = int(pid)
            except (TypeError, ValueError):
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.urlencode()
        ctx["cancel_url"] = reverse("plantacao_list") + (f"?{q}" if q else "")
        return ctx

    def get_success_url(self):
        return reverse("plantacao_list")


class PlantacaoUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_plantacao",)
    model = Plantacao
    form_class = PlantacaoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar plantação"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("plantacao_list")
        return ctx

    def get_success_url(self):
        return reverse("plantacao_list")


class PlantacaoDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_plantacao",)
    model = Plantacao
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("plantacao_list")
        return ctx

    def get_success_url(self):
        return reverse("plantacao_list")


# --- Compra ---
class CompraListView(PortalAccessMixin, PropriedadeFilteredMixin, ListView):
    permission_required = ("api.view_compra",)
    model = Compra
    template_name = "api/portal/compra_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        return super().get_queryset().select_related("propriedade", "insumo")


class CompraCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_compra",)
    model = Compra
    form_class = CompraForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Nova compra"}

    def get_initial(self):
        initial = super().get_initial()
        pid = self.request.GET.get("propriedade")
        if pid:
            try:
                initial["propriedade"] = int(pid)
            except (TypeError, ValueError):
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.urlencode()
        ctx["cancel_url"] = reverse("compra_list") + (f"?{q}" if q else "")
        return ctx

    def get_success_url(self):
        return reverse("compra_list")


class CompraUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_compra",)
    model = Compra
    form_class = CompraForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar compra"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("compra_list")
        return ctx

    def get_success_url(self):
        return reverse("compra_list")


class CompraDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_compra",)
    model = Compra
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("compra_list")
        return ctx

    def get_success_url(self):
        return reverse("compra_list")


# --- Venda ---
class VendaListView(PortalAccessMixin, PropriedadeFilteredMixin, ListView):
    permission_required = ("api.view_venda",)
    model = Venda
    template_name = "api/portal/venda_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        return super().get_queryset().select_related("propriedade", "produto")


class VendaCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_venda",)
    model = Venda
    form_class = VendaForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Nova venda"}

    def get_initial(self):
        initial = super().get_initial()
        pid = self.request.GET.get("propriedade")
        if pid:
            try:
                initial["propriedade"] = int(pid)
            except (TypeError, ValueError):
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.urlencode()
        ctx["cancel_url"] = reverse("venda_list") + (f"?{q}" if q else "")
        return ctx

    def get_success_url(self):
        return reverse("venda_list")


class VendaUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_venda",)
    model = Venda
    form_class = VendaForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar venda"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("venda_list")
        return ctx

    def get_success_url(self):
        return reverse("venda_list")


class VendaDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_venda",)
    model = Venda
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("venda_list")
        return ctx

    def get_success_url(self):
        return reverse("venda_list")


# --- Aplicação insumo ---
class AplicacaoFilteredMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        pl = self.request.GET.get("plantacao")
        if pl:
            try:
                qs = qs.filter(plantacao_id=int(pl))
            except (TypeError, ValueError):
                pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pl = self.request.GET.get("plantacao")
        ctx["filter_plantacao_id"] = pl
        if pl:
            try:
                ctx["filter_plantacao"] = Plantacao.objects.select_related(
                    "propriedade", "produto"
                ).filter(pk=int(pl)).first()
            except (TypeError, ValueError):
                pass
        return ctx


class AplicacaoListView(PortalAccessMixin, AplicacaoFilteredMixin, ListView):
    permission_required = ("api.view_aplicacaoinsumo",)
    model = AplicacaoInsumo
    template_name = "api/portal/aplicacao_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        return super().get_queryset().select_related("plantacao", "plantacao__propriedade", "insumo")


class AplicacaoCreateView(PortalAccessMixin, CreateView):
    permission_required = ("api.add_aplicacaoinsumo",)
    model = AplicacaoInsumo
    form_class = AplicacaoInsumoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Nova aplicação de insumo"}

    def get_initial(self):
        initial = super().get_initial()
        pl = self.request.GET.get("plantacao")
        if pl:
            try:
                initial["plantacao"] = int(pl)
            except (TypeError, ValueError):
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.urlencode()
        ctx["cancel_url"] = reverse("aplicacao_list") + (f"?{q}" if q else "")
        return ctx

    def get_success_url(self):
        return reverse("aplicacao_list")


class AplicacaoUpdateView(PortalAccessMixin, UpdateView):
    permission_required = ("api.change_aplicacaoinsumo",)
    model = AplicacaoInsumo
    form_class = AplicacaoInsumoForm
    template_name = "api/portal/object_form.html"
    extra_context = {"page_title": "Editar aplicação"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("aplicacao_list")
        return ctx

    def get_success_url(self):
        return reverse("aplicacao_list")


class AplicacaoDeleteView(PortalAccessMixin, DeleteView):
    permission_required = ("api.delete_aplicacaoinsumo",)
    model = AplicacaoInsumo
    template_name = "api/portal/object_confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse("aplicacao_list")
        return ctx

    def get_success_url(self):
        return reverse("aplicacao_list")


class AlertaListView(PortalAccessMixin, ListView):
    permission_required = ("api.view_alerta",)
    model = Alerta
    template_name = "api/portal/alerta_list.html"
    context_object_name = "object_list"


@login_required
@permission_required("api.change_alerta", raise_exception=True)
def alerta_marcar_lida_view(request, pk):
    if request.method != "POST":
        return redirect("alerta_list")
    alerta = get_object_or_404(Alerta, pk=pk)
    alerta.lido = True
    alerta.save(update_fields=["lido"])
    return redirect("alerta_list")


@login_required
@permission_required("api.view_propriedade", raise_exception=True)
def relatorios_view(request):
    sincronizar_alertas_financeiros()
    total_compras = sum((c.total() for c in Compra.objects.all()), Decimal("0"))
    total_vendas = sum((v.total() for v in Venda.objects.all()), Decimal("0"))
    props = Propriedade.objects.all()
    por_propriedade = []
    for p in props:
        vc = Venda.objects.filter(propriedade=p)
        cc = Compra.objects.filter(propriedade=p)
        sv = sum((x.total() for x in vc), Decimal("0"))
        sc = sum((x.total() for x in cc), Decimal("0"))
        por_propriedade.append(
            {
                "propriedade": p,
                "total_vendas": sv,
                "total_compras": sc,
                "n_plantacoes": Plantacao.objects.filter(propriedade=p).count(),
            }
        )
    context = {
        "n_propriedades": Propriedade.objects.count(),
        "n_produtos": Produto.objects.count(),
        "n_insumos": Insumo.objects.count(),
        "n_plantacoes": Plantacao.objects.count(),
        "n_compras": Compra.objects.count(),
        "n_vendas": Venda.objects.count(),
        "n_aplicacoes": AplicacaoInsumo.objects.count(),
        "total_compras": total_compras,
        "total_vendas": total_vendas,
        "por_propriedade": por_propriedade,
    }
    return render(request, "api/portal/relatorios.html", context)


@login_required
@permission_required("api.view_propriedade", raise_exception=True)
def relatorio_export_csv_view(request):
    sincronizar_alertas_financeiros()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="relatorio_agro.csv"'
    response.write("\ufeff")
    w = csv.writer(response)
    w.writerow(["PROPRIEDADES"])
    w.writerow(["nome", "codigo", "localizacao", "area_total"])
    for p in Propriedade.objects.all():
        w.writerow([p.nome, p.codigo, p.localizacao or "", p.area_total])
    w.writerow([])
    w.writerow(["COMPRAS"])
    w.writerow(["data", "propriedade", "insumo", "quantidade", "unidade", "preco_unitario", "total"])
    for c in Compra.objects.select_related("propriedade", "insumo").all():
        w.writerow(
            [
                c.data_compra.isoformat(),
                c.propriedade.nome,
                c.insumo.nome,
                c.quantidade,
                c.unidade,
                c.preco_unitario,
                c.total(),
            ]
        )
    w.writerow([])
    w.writerow(["VENDAS"])
    w.writerow(["data", "propriedade", "produto", "quantidade", "unidade", "preco_unitario", "total"])
    for v in Venda.objects.select_related("propriedade", "produto").all():
        w.writerow(
            [
                v.data_venda.isoformat(),
                v.propriedade.nome,
                v.produto.nome,
                v.quantidade,
                v.unidade,
                v.preco_unitario,
                v.total(),
            ]
        )
    return response


@login_required
@permission_required("api.view_propriedade", raise_exception=True)
def relatorio_export_pdf_view(request):
    sincronizar_alertas_financeiros()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Relatório Agro")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Relatório consolidado — gestão rural", styles["Title"]),
        Spacer(1, 12),
    ]
    total_c = sum((c.total() for c in Compra.objects.all()), Decimal("0"))
    total_v = sum((v.total() for v in Venda.objects.all()), Decimal("0"))
    story.append(Paragraph(f"<b>Total compras:</b> {total_c}", styles["Normal"]))
    story.append(Paragraph(f"<b>Total vendas:</b> {total_v}", styles["Normal"]))
    story.append(Spacer(1, 16))
    data = [["Propriedade", "Compras", "Vendas", "Plantações"]]
    for p in Propriedade.objects.all():
        sc = sum((x.total() for x in Compra.objects.filter(propriedade=p)), Decimal("0"))
        sv = sum((x.total() for x in Venda.objects.filter(propriedade=p)), Decimal("0"))
        data.append(
            [
                p.nome,
                str(sc),
                str(sv),
                str(Plantacao.objects.filter(propriedade=p).count()),
            ]
        )
    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d7a55")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(t)
    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relatorio_agro.pdf"'
    return response
