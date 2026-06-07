# Kubernetes – Agro SaaS Multi-Tenant

Ordem sugerida para aplicar os manifests (namespace primeiro, depois banco, depois app):

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml
# Aguardar PostgreSQL ficar Ready antes do Django
kubectl wait --for=condition=ready pod -l app=postgres -n agro-saas --timeout=120s
kubectl apply -f django-deployment.yaml
kubectl apply -f django-service.yaml
kubectl apply -f hpa.yaml
kubectl apply -f ingress.yaml   # opcional; requer Ingress Controller
```

**Build da imagem Django:** antes do deploy, build e push da imagem (ex.: `agro-api:latest`):

```bash
docker build -t agro-api:latest .
# Se usar registry: docker tag agro-api:latest seu-registry/agro-api:v1 && docker push ...
# Atualize django-deployment.yaml (image + imagePullPolicy) para apontar ao registry.
```

Em **django-deployment.yaml** e **postgres-statefulset.yaml**, ajuste a imagem e o `storageClassName` conforme seu cluster.

## Saúde dos pods (`/healthz/`)

A aplicação expõe **`GET /healthz/`** (resposta `OK`, sem consultar o banco). Os probes do Deployment enviam **`Host: agro.local`**, que deve constar em **`ALLOWED_HOSTS`** no ConfigMap (junto com `*.agro.local` via sufixo `.agro.local`). Se mudar o domínio do Ingress, alinhe `ALLOWED_HOSTS`, **`TENANT_SUBDOMAIN_BASE`** e o header `Host` nos probes.

## Migrações (init container)

O init executa **`migrate_schemas --noinput`**, que aplica **shared + tenants** já cadastrados. O schema `public` continua sendo migrado primeiro; inquilinos novos continuam exigindo fluxo no admin (ou comando) para criar schema/domínio.

## HPA

O **HorizontalPodAutoscaler** precisa de **metrics-server** (ou equivalente) no cluster; sem métricas de CPU/memória, o HPA não escala.

## `postgres-pvc.yaml`

O StatefulSet já cria PVC via **`volumeClaimTemplates`**. O arquivo `postgres-pvc.yaml` é apenas referência; não é necessário aplicá-lo junto com o StatefulSet, salvo se você optar por Postgres sem StatefulSet.

## Ingress multi-tenant

Para subdomínios (`fazenda1.agro.local`), inclua regras ou **`*.agro.local`** no Ingress e resolva DNS (wildcard). Ative **TLS** quando for produção.
