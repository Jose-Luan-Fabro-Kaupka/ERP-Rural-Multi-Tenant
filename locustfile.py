"""
Teste de carga na API multi-tenant (Locust).

Uso típico:
  pip install -r requirements-dev.txt
  export LOCUST_USERNAME=seu_usuario
  export LOCUST_PASSWORD=sua_senha
  # apontando direto para uma máquina/porta pública:
  ./scripts/run_loadtest.sh --users 30 --spawn-rate 5 --run-time 2m
  # ou apontando para 127.0.0.1:8080 e injetando o Host do tenant:
  LOCUST_TENANT_HOST=loadtest.localhost \
    .venv/bin/locust -f locustfile.py --host=http://127.0.0.1:8080 --headless \
      -u 10 -r 2 -t 2m

Com JWT preenchido, os endpoints autenticados passam a retornar 200 em vez de 401/403.
Sem credenciais, o teste ainda exercita latência e roteamento (útil para stress do Ingress/HPA).

Se `LOCUST_TENANT_HOST` estiver definido, o header HTTP `Host` é sobrescrito nas
requisições. Isso permite apontar a URL base para um IP/porta (ex.: `kubectl
port-forward` para 127.0.0.1:8080) e ainda assim ativar o roteamento do
django-tenants pelo domínio do inquilino.
"""
import os

from locust import HttpUser, between, task


class AgroAPIUser(HttpUser):
    wait_time = between(0.5, 2.5)

    def on_start(self):
        self.token = None
        self.tenant_host = os.environ.get("LOCUST_TENANT_HOST", "").strip()
        user = os.environ.get("LOCUST_USERNAME", "").strip()
        password = os.environ.get("LOCUST_PASSWORD", "").strip()
        if not user or not password:
            return
        resp = self.client.post(
            "/api/auth/token/",
            json={"username": user, "password": password},
            headers=self._auth_headers(),
            name="/api/auth/token/",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access")

    def _auth_headers(self):
        h = {"Content-Type": "application/json"}
        if self.tenant_host:
            h["Host"] = self.tenant_host
        return h

    def _headers(self):
        h = self._auth_headers()
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
