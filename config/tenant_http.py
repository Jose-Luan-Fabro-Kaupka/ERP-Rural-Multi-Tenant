"""
Respostas HTTP quando o Host não corresponde a nenhum Domain (django-tenants).
"""
from django.http import HttpResponseNotFound


def tenant_not_found_view(request):
    host = request.get_host().split(":")[0]
    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Domínio não cadastrado</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 38rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    code {{ background: #f0f0f0; padding: 0.15rem 0.35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Nenhum inquilino para este endereço</h1>
  <p>O host <strong>{host}</strong> não está cadastrado em <strong>Customers → Domains</strong>
     (schema público). Sem isso, o Django não usa as URLs do tenant (<code>/registrar/</code>, <code>/api/</code>, etc.).</p>
  <p><strong>O que fazer:</strong> no admin em <a href="http://127.0.0.1:8000/admin/customers/domain/add/">/admin/</a>,
     crie um <em>Domain</em> com o campo <strong>domain</strong> exatamente igual a:</p>
  <p><code>{host}</code></p>
  <p>Use o mesmo texto que aparece na barra de endereço <strong>sem a porta</strong> (ex.: <code>fazenda1.localhost</code>),
     em minúsculas, e associe ao <em>Client</em> certo.</p>
</body>
</html>"""
    return HttpResponseNotFound(html)
