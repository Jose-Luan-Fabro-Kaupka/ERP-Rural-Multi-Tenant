# Arquitetura Multi-Tenant para Gestão de Propriedades Rurais

Este repositório contém o projeto desenvolvido como parte do Trabalho de Conclusão de Curso em Engenharia de Software, cujo objetivo é propor e implementar uma arquitetura **multi-tenant** aplicada a um sistema de gestão de propriedades rurais.

A aplicação foi desenvolvida com **Django**, **PostgreSQL** e **django-tenants**, utilizando o modelo de isolamento **schema-per-tenant**, no qual cada inquilino possui seus próprios dados armazenados em um schema separado dentro do mesmo banco de dados. A proposta busca avaliar a viabilidade técnica dessa abordagem em relação ao isolamento de dados, organização da aplicação, manutenção, escalabilidade e implantação em ambiente conteinerizado.

---

## Objetivo do Projeto

O objetivo geral deste trabalho é implementar e avaliar uma arquitetura multi-tenant para um sistema de gestão rural, permitindo que diferentes propriedades, clientes ou organizações utilizem a mesma instância da aplicação, mantendo o isolamento lógico dos dados de cada inquilino.

Entre os objetivos específicos estão:

- investigar o uso de arquiteturas multi-tenant em aplicações web;
- implementar isolamento de dados por meio de schemas PostgreSQL;
- desenvolver uma API REST para as funcionalidades principais do sistema;
- utilizar autenticação e autorização para controle de acesso;
- preparar a aplicação para execução com Docker e Kubernetes;
- realizar testes unitários, testes de integração e testes de carga;
- avaliar a aderência da implementação aos requisitos definidos no trabalho.

---

## Visão Geral da Arquitetura

A aplicação utiliza uma arquitetura multi-tenant baseada no modelo **schema-per-tenant**.

Nesse modelo, há um único banco de dados PostgreSQL, mas cada inquilino possui um schema próprio. O schema `public` armazena informações globais da aplicação, como os dados dos tenants e seus domínios. Já os schemas individuais armazenam as entidades de negócio de cada tenant, como propriedades, produtos, insumos, plantações, compras e vendas.

O roteamento entre os tenants é realizado com base no domínio ou subdomínio acessado pelo usuário. O middleware do `django-tenants` identifica o tenant correspondente à requisição e direciona as operações do ORM para o schema apropriado.

Essa abordagem permite que múltiplos clientes compartilhem a mesma aplicação, mantendo separação lógica entre seus dados.

---

## Tecnologias Utilizadas

As principais tecnologias utilizadas no projeto são:

- **Python**
- **Django**
- **Django REST Framework**
- **django-tenants**
- **PostgreSQL**
- **Simple JWT**
- **Docker**
- **Docker Compose**
- **Kubernetes**
- **Locust**
- **Coverage**

O Django foi utilizado como framework principal da aplicação. O PostgreSQL foi escolhido por oferecer suporte nativo a schemas, recurso fundamental para a implementação do isolamento multi-tenant. A biblioteca `django-tenants` foi utilizada para gerenciar a separação entre tenants, enquanto o Django REST Framework permitiu a construção da API REST.

Docker e Kubernetes foram utilizados para preparar a aplicação para execução em ambientes conteinerizados e escaláveis. O Locust foi empregado para testes de carga, e o Coverage para análise da cobertura dos testes automatizados.

---

## Funcionalidades Implementadas

O sistema contempla funcionalidades relacionadas à gestão de propriedades rurais, incluindo:

- cadastro e gerenciamento de propriedades;
- cadastro de produtos;
- cadastro de insumos;
- registro de plantações;
- controle de compras;
- controle de vendas;
- registro de aplicações de insumos;
- autenticação via JWT;
- autorização baseada em permissões;
- geração de relatórios em CSV e PDF;
- painel administrativo para gerenciamento de tenants;
- endpoint de verificação de saúde da aplicação;
- suporte a execução com Docker e Kubernetes.

A parte relacionada a IoT foi desconsiderada na versão final do relatório, pois foi removida do escopo do trabalho.

---

## Estrutura Geral do Projeto

A estrutura principal do projeto está organizada da seguinte forma:

```text
.
├── api/                    # Aplicação de negócio executada nos schemas dos tenants
├── config/                 # Configurações principais do Django
├── customers/              # Gerenciamento de tenants e domínios no schema público
├── k8s/                    # Arquivos de configuração para Kubernetes
├── scripts/                # Scripts auxiliares
├── templates/              # Templates HTML utilizados pela aplicação
├── docker-compose.yml      # Configuração para ambiente Docker
├── Dockerfile              # Imagem da aplicação
├── locustfile.py           # Definição dos testes de carga
├── manage.py               # Utilitário de gerenciamento do Django
├── requirements.txt        # Dependências principais
└── requirements-dev.txt    # Dependências de desenvolvimento e testes
```

---

## Modelo Multi-Tenant

O projeto utiliza o modelo **schema-per-tenant**, no qual:

- o schema `public` armazena informações compartilhadas;
- cada tenant possui um schema próprio;
- as tabelas da aplicação de negócio são criadas separadamente em cada schema;
- o domínio acessado define qual tenant será utilizado;
- os dados de um tenant não são acessados por outro tenant.

Esse modelo oferece maior isolamento lógico em comparação com abordagens baseadas apenas em uma coluna identificadora de tenant, reduzindo o risco de vazamento acidental de dados entre clientes.

---

## API REST

A API REST disponibiliza endpoints para as principais entidades do sistema.

Exemplos de recursos disponíveis:

```text
/api/auth/token/
/api/auth/token/refresh/
/api/propriedades/
/api/produtos/
/api/insumos/
/api/plantacoes/
/api/compras/
/api/vendas/
/api/aplicacoes/
/api/alertas/
```

Os endpoints utilizam autenticação JWT e permissões do Django para controlar o acesso aos recursos.

---

## Execução com Docker

Para executar a aplicação em ambiente Docker, pode-se utilizar:

```bash
docker-compose up -d
```

Esse comando inicializa os serviços definidos no `docker-compose.yml`, incluindo a aplicação Django e o banco de dados PostgreSQL.

Após a inicialização, as migrações podem ser executadas com:

```bash
docker-compose exec api python manage.py migrate_schemas --shared
docker-compose exec api python manage.py migrate_schemas
```

Para criar um superusuário:

```bash
docker-compose exec api python manage.py createsuperuser
```

---

## Testes

Foram realizados testes unitários, testes de integração e testes de carga.

A suíte automatizada contempla:

- criação de entidades do domínio;
- validação de regras básicas dos modelos;
- verificação de isolamento entre tenants;
- testes de acesso a relatórios;
- validação de exportação em CSV;
- validação de exportação em PDF;
- verificação do endpoint de saúde da aplicação.

Para executar os testes:

```bash
python manage.py test api.tests
```

Também foi utilizada a ferramenta Coverage para medir a cobertura dos testes:

```bash
coverage run --source=api,customers,config manage.py test api.tests
coverage report --skip-empty
```

A execução da suíte registrou 11 testes aprovados e cobertura global de aproximadamente 70%.

---

## Testes de Carga

Os testes de carga foram definidos com o Locust, simulando múltiplos usuários acessando a API da aplicação.

Para executar:

```bash
locust -f locustfile.py --host=http://tenant1.localhost:8000
```

A partir disso, a interface do Locust pode ser acessada em:

```text
http://localhost:8089
```

Esses testes foram utilizados para avaliar o comportamento da aplicação sob múltiplas requisições simultâneas, especialmente no contexto de roteamento multi-tenant e escalabilidade horizontal.

---

## Implantação com Kubernetes

O projeto inclui arquivos de configuração para Kubernetes, localizados no diretório `k8s/`.

A infraestrutura contempla:

- Deployment da aplicação Django;
- StatefulSet para o PostgreSQL;
- Service para comunicação entre os componentes;
- ConfigMap e Secret;
- Ingress;
- Horizontal Pod Autoscaler;
- Persistent Volume Claim para persistência do banco.

Esses arquivos permitem simular uma implantação mais próxima de um ambiente de produção, com suporte a escalabilidade e separação entre configuração, aplicação e banco de dados.

---

## Resultados Obtidos

Os testes realizados indicaram que a arquitetura implementada atende ao objetivo proposto. O isolamento entre tenants foi validado por testes de integração, demonstrando que dados cadastrados em um tenant não são acessíveis a partir de outro.

A API REST foi implementada para as principais entidades do sistema, e a aplicação foi preparada para execução em ambiente conteinerizado. A geração de relatórios em CSV e PDF também foi validada por testes automatizados.

A cobertura global de testes foi de aproximadamente 70%, com maior cobertura nos componentes centrais da aplicação, como modelos, serializers, views e rotas da API.

---

## Considerações Finais

O projeto demonstrou a viabilidade técnica de uma arquitetura multi-tenant para sistemas de gestão rural. O uso de schemas PostgreSQL permitiu separar os dados de cada tenant de forma clara, enquanto o Django e o `django-tenants` forneceram suporte adequado para roteamento, migrações e organização da aplicação.

A solução apresenta potencial de evolução para cenários reais, especialmente em contextos nos quais diferentes propriedades, cooperativas ou organizações rurais necessitam utilizar uma mesma plataforma sem compartilhar diretamente seus dados.

Como trabalhos futuros, podem ser considerados:

- ampliação da cobertura de testes;
- aprimoramento da interface web;
- melhoria dos mecanismos de autorização por papéis;
- implantação em ambiente de nuvem;
- monitoramento com métricas em tempo real;
- refinamento dos relatórios gerenciais;
- análise comparativa com outros modelos de multi-tenancy.

---

## Autor

José Luan Fabro Kaupka

Trabalho de Conclusão de Curso em Engenharia de Software  
Universidade Tecnológica Federal do Paraná — Câmpus Dois Vizinhos

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos.