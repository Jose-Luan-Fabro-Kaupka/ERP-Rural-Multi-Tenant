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


import json

from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Alerta
from customers.models import GlobalConfig


class JWTAuthTest(TenantTestCase):
    """Autenticação JWT no domínio do tenant (RA4)."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        User = get_user_model()
        self.user = User.objects.create_user(username="jwtuser", password="segredo123")

    def test_token_obtain_retorna_access_e_refresh(self):
        r = self.client.post(
            "/api/auth/token/",
            data=json.dumps({"username": "jwtuser", "password": "segredo123"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)

    def test_token_credenciais_invalidas(self):
        r = self.client.post(
            "/api/auth/token/",
            data=json.dumps({"username": "jwtuser", "password": "errada"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)


class PropriedadeAPITest(TenantTestCase):
    """API REST de Propriedade com permissões por modelo (RA1, RA4)."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="apiadmin", password="segredo123", email="a@a.com"
        )
        token = RefreshToken.for_user(self.user).access_token
        self.auth = f"Bearer {token}"

    def test_api_exige_autenticacao(self):
        r = self.client.get("/api/propriedades/")
        self.assertIn(r.status_code, (401, 403))

    def test_api_lista_autenticada(self):
        Propriedade.objects.create(nome="Sítio API", codigo="API1", area_total=Decimal("10.00"))
        r = self.client.get("/api/propriedades/", HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_api_cria_propriedade(self):
        antes = Propriedade.objects.count()
        r = self.client.post(
            "/api/propriedades/",
            data=json.dumps({"nome": "Nova", "codigo": "NV1", "area_total": "42.00"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Propriedade.objects.count(), antes + 1)

    def test_api_busca_por_nome(self):
        Propriedade.objects.create(nome="Fazenda Norte", codigo="N1", area_total=Decimal("10.00"))
        Propriedade.objects.create(nome="Fazenda Sul", codigo="S1", area_total=Decimal("10.00"))
        r = self.client.get("/api/propriedades/?search=Norte", HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(r.status_code, 200)
        nomes = [p["nome"] for p in r.json()]
        self.assertEqual(nomes, ["Fazenda Norte"])


class ModelComportamentoTest(TenantTestCase):
    """Regras de negócio dos models (totais, representação e unicidade)."""

    def _propriedade(self):
        return Propriedade.objects.create(
            nome="Base", codigo="B1", area_total=Decimal("100.00")
        )

    def test_compra_total(self):
        prop = self._propriedade()
        ins = Insumo.objects.create(nome="Adubo", tipo="Químico")
        compra = Compra.objects.create(
            propriedade=prop, insumo=ins, quantidade=Decimal("3"),
            unidade="kg", preco_unitario=Decimal("10.00"), data_compra=date(2024, 1, 1),
        )
        self.assertEqual(compra.total(), Decimal("30.00"))

    def test_venda_total(self):
        prop = self._propriedade()
        prod = Produto.objects.create(nome="Trigo", unidade="t")
        venda = Venda.objects.create(
            propriedade=prop, produto=prod, quantidade=Decimal("4"),
            unidade="t", preco_unitario=Decimal("25.00"), data_venda=date(2024, 2, 1),
        )
        self.assertEqual(venda.total(), Decimal("100.00"))

    def test_str_dos_models(self):
        prop = self._propriedade()
        prod = Produto.objects.create(nome="Café", unidade="kg")
        ins = Insumo.objects.create(nome="Calcário", tipo="Corretivo")
        plant = Plantacao.objects.create(
            propriedade=prop, produto=prod, talhao="T1",
            area=Decimal("5.00"), data_inicio=date(2024, 3, 1),
        )
        self.assertEqual(str(prod), "Café")
        self.assertEqual(str(ins), "Calcário")
        self.assertIn("Café", str(plant))
        self.assertIn("T1", str(plant))

    def test_codigo_propriedade_unico(self):
        self._propriedade()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Propriedade.objects.create(
                    nome="Outra", codigo="B1", area_total=Decimal("5.00")
                )


class AlertaTest(TenantTestCase):
    """Model de alertas: default, ordenação e representação."""

    def test_severidade_default_e_ordenacao(self):
        a1 = Alerta.objects.create(titulo="Primeiro", mensagem="m1")
        a2 = Alerta.objects.create(titulo="Segundo", mensagem="m2")
        self.assertEqual(a1.severidade, Alerta.Severidade.AVISO)
        self.assertEqual(list(Alerta.objects.all()), [a2, a1])

    def test_alerta_str(self):
        a = Alerta.objects.create(
            titulo="Estoque baixo", mensagem="verifique", severidade=Alerta.Severidade.CRITICO
        )
        self.assertEqual(str(a), "Estoque baixo")


class GlobalConfigTest(TenantTestCase):
    """Configuração global é um singleton (sempre pk=1)."""

    def test_singleton(self):
        c1 = GlobalConfig.get_solo()
        c1.max_tenants = 7
        c1.save()
        c2 = GlobalConfig.get_solo()
        self.assertEqual(c1.pk, 1)
        self.assertEqual(c2.pk, 1)
        self.assertEqual(c2.max_tenants, 7)
        self.assertEqual(GlobalConfig.objects.count(), 1)
