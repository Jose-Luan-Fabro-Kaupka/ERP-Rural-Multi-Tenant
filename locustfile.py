"""
Teste de carga na API multi-tenant (Locust).

Uso típico:
  pip install -r requirements-dev.txt
  export LOCUST_USERNAME=seu_usuario
  export LOCUST_PASSWORD=sua_senha
  ./scripts/run_loadtest.sh --users 30 --spawn-rate 5 --run-time 2m

Com JWT preenchido, os endpoints autenticados passam a retornar 200 em vez de 401/403.
Sem credenciais, o teste ainda exercita latência e roteamento (útil para stress do Ingress/HPA).
"""
import os

from locust import HttpUser, between, task


class AgroAPIUser(HttpUser):
    wait_time = between(0.5, 2.5)

    def on_start(self):
        self.token = None
        user = os.environ.get("LOCUST_USERNAME", "").strip()
        password = os.environ.get("LOCUST_PASSWORD", "").strip()
        if not user or not password:
            return
        resp = self.client.post(
            "/api/auth/token/",
            json={"username": user, "password": password},
            headers={"Content-Type": "application/json"},
            name="/api/auth/token/",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access")

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    @task(4)
    def list_propriedades(self):
        self.client.get("/api/propriedades/", headers=self._headers(), name="/api/propriedades/")

    @task(3)
    def list_produtos(self):
        self.client.get("/api/produtos/", headers=self._headers(), name="/api/produtos/")

    @task(3)
    def list_insumos(self):
        self.client.get("/api/insumos/", headers=self._headers(), name="/api/insumos/")

    @task(2)
    def list_plantacoes(self):
        self.client.get("/api/plantacoes/", headers=self._headers(), name="/api/plantacoes/")

    @task(2)
    def list_alertas(self):
        self.client.get("/api/alertas/", headers=self._headers(), name="/api/alertas/")
