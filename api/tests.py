"""
Testes unitários e de integração para o módulo API.
Garantem isolamento de dados entre inquilinos (multi-tenant).
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import tenant_context, get_tenant_model

from config.views_health import healthz_view

from .models import Propriedade, Produto, Insumo, Plantacao, Compra, Venda, AplicacaoInsumo


class PropriedadeModelTest(TenantTestCase):
    """Testes do model Propriedade no contexto de um tenant."""

    def test_criar_propriedade(self):
        Propriedade.objects.create(
            nome="Fazenda Teste",
            codigo="FT001",
            area_total=Decimal("100.00"),
        )
        self.assertEqual(Propriedade.objects.count(), 1)
        p = Propriedade.objects.get(codigo="FT001")
        self.assertEqual(p.nome, "Fazenda Teste")

    def test_propriedade_str(self):
        p = Propriedade.objects.create(nome="Talhão A", codigo="TA1", area_total=Decimal("50.00"))
        self.assertIn("Talhão A", str(p))


class ProdutoInsumoModelTest(TenantTestCase):
    """Testes dos models Produto e Insumo."""

    def test_criar_produto_e_insumo(self):
        prod = Produto.objects.create(nome="Soja", unidade="kg")
        ins = Insumo.objects.create(nome="Semente Soja", tipo="Semente")
        self.assertEqual(Produto.objects.get(nome="Soja").unidade, "kg")
        self.assertEqual(Insumo.objects.get(nome="Semente Soja").tipo, "Semente")


class IsolamentoEntreTenantsTest(TestCase):
    """
    Testes de integração: verifica que dados de um inquilino
    não ficam acessíveis a outro (isolamento por schema).
    """

    def test_isolamento_propriedades_entre_tenants(self):
        from django.core.management import call_command
        Tenant = get_tenant_model()
        from customers.models import Domain

        # Garante schema public migrado
        call_command("migrate_schemas", "--shared", verbosity=0, interactive=False)

        # Cria tenant 1 e migra seu schema
        tenant1 = Tenant(
            schema_name="tenant1",
            name="Tenant Um",
        )
        tenant1.save()
        Domain(domain="tenant1.localhost", tenant=tenant1, is_primary=True).save()
        call_command("migrate_schemas", schema_name="tenant1", verbosity=0, interactive=False)

        with tenant_context(tenant1):
            Propriedade.objects.create(
                nome="Fazenda Tenant 1",
                codigo="F1",
                area_total=Decimal("200.00"),
            )
            self.assertEqual(Propriedade.objects.count(), 1)

        # Cria tenant 2 e migra seu schema
        tenant2 = Tenant(
            schema_name="tenant2",
            name="Tenant Dois",
        )
        tenant2.save()
        Domain(domain="tenant2.localhost", tenant=tenant2, is_primary=True).save()
        call_command("migrate_schemas", schema_name="tenant2", verbosity=0, interactive=False)

        with tenant_context(tenant2):
            # Tenant 2 não deve ver a propriedade do tenant 1
            self.assertEqual(Propriedade.objects.count(), 0)
            Propriedade.objects.create(
                nome="Fazenda Tenant 2",
                codigo="F2",
                area_total=Decimal("150.00"),
            )
            self.assertEqual(Propriedade.objects.count(), 1)
            self.assertEqual(Propriedade.objects.get(codigo="F2").nome, "Fazenda Tenant 2")

        # De volta ao tenant 1, a propriedade dele continua lá
        with tenant_context(tenant1):
            self.assertEqual(Propriedade.objects.count(), 1)
            self.assertEqual(Propriedade.objects.get(codigo="F1").nome, "Fazenda Tenant 1")


class RelatoriosWebTest(TenantTestCase):
    """Portal web: página de relatórios e exportações CSV/PDF."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        User = get_user_model()
        self.user = User.objects.create_user(username="reluser", password="secret123")
        ct = ContentType.objects.get_for_model(Propriedade)
        view_prop = Permission.objects.get(content_type=ct, codename="view_propriedade")
        self.user.user_permissions.add(view_prop)

        self.prop = Propriedade.objects.create(
            nome="Fazenda Rel",
            codigo="REL01",
            area_total=Decimal("80.00"),
        )
        self.prod = Produto.objects.create(nome="Milho", unidade="t")
        self.ins = Insumo.objects.create(nome="Fertilizante X", tipo="Químico")
        Plantacao.objects.create(
            propriedade=self.prop,
            produto=self.prod,
            area=Decimal("10.00"),
            data_inicio=date(2024, 3, 1),
        )
        Compra.objects.create(
            propriedade=self.prop,
            insumo=self.ins,
            quantidade=Decimal("2"),
            unidade="t",
            preco_unitario=Decimal("100.00"),
            data_compra=date(2024, 4, 1),
        )
        Venda.objects.create(
            propriedade=self.prop,
            produto=self.prod,
            quantidade=Decimal("5"),
            unidade="t",
            preco_unitario=Decimal("200.00"),
            data_venda=date(2024, 5, 1),
        )

    def test_relatorios_anonimo_redireciona_login(self):
        r = self.client.get("/relatorios/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r["Location"])

    def test_relatorios_sem_permissao_403(self):
        User = get_user_model()
        nop = User.objects.create_user(username="noperm", password="secret123")
        self.client.login(username="noperm", password="secret123")
        r = self.client.get("/relatorios/")
        self.assertEqual(r.status_code, 403)

    def test_relatorios_autenticado_mostra_totais(self):
        self.client.login(username="reluser", password="secret123")
        r = self.client.get("/relatorios/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Fazenda Rel")
        self.assertContains(r, "200")  # total compras: 2 × 100
        self.assertContains(r, "1000")  # total vendas: 5 × 200

    def test_export_csv_utf8_bom_e_linhas(self):
        self.client.login(username="reluser", password="secret123")
        r = self.client.get("/relatorios/exportar/csv/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        body = r.content.decode("utf-8-sig")
        self.assertTrue(body.startswith("PROPRIEDADES"))
        self.assertIn("Fazenda Rel", body)
        self.assertIn("REL01", body)
        self.assertIn("COMPRAS", body)
        self.assertIn("Fertilizante X", body)
        self.assertIn("VENDAS", body)
        self.assertIn("Milho", body)

    def test_export_pdf_bytes_magic(self):
        self.client.login(username="reluser", password="secret123")
        r = self.client.get("/relatorios/exportar/pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))


class HealthzViewTest(SimpleTestCase):
    def test_healthz_view_resposta(self):
        from django.http import HttpRequest

        req = HttpRequest()
        resp = healthz_view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"OK\n")


class HealthzTenantUrlTest(TenantTestCase):
    def test_healthz_no_portal_tenant(self):
        client = TenantClient(self.tenant)
        r = client.get("/healthz/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content.strip(), b"OK")
