# 🚀 Sistema de ETL de CriptoMoedas  com Streamlit

![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Prefect](https://img.shields.io/badge/Prefect-ETL%20Orchestration-2E77BC) ![Render](https://img.shields.io/badge/Render-Deployed-2E77BC) ![MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Índice
  - [📋 Sobre o Projeto](#-sobre-o-projeto)
  - [✨ Funcionalidades Principais](#-funcionalidades-principais)
  - [🏗️ Arquitetura do Sistema](#️-arquitetura-do-sistema)
  - [🔄 Pipeline ETL](#-pipeline-etl)
  - [📊 Aplicação Streamlit](#-aplicação-streamlit)
  - [🗂️ Estrutura do Projeto](#-estrutura-do-projeto)
  - [🚀 Deploy no Render](#-deploy-na-render)
  - [☁️ Orquestração com Prefect Cloud](#️-orquestração-com-prefect-cloud)
  - [🛠️ Configuração do Ambiente Local](#️-configuração-do-ambiente-local)
  - [🔐 Variáveis de Ambiente](#-variáveis-de-ambiente)
  - [🧪 Qualidade de Código](#-qualidade-de-código)
  - [📄 Licença](#-licença)

## 📋 Sobre o Projeto

O FINOPSETL é uma plataforma de engenahria de dados de **Criptomoedas** que integra:

- Pipeline ETL automatizado
- Orquestração com Prefect Cloud
- Dashboard interativo em Streamlit
- Deploy em nuvem via Render

O sistema coleta os dados da api **coingecko**, processa e armazena em banco de dados, permitindo visualização e análise por meio de uma aplicação web.

É um projeto focado em **Data Engineering** e boas práticas de produção.

## ✨ Funcionalidades Principais

- Pipeline ETL automatizado
- Orquestração de fluxos com Prefect Cloud
- Dashboard interativo em tempo real com Streamlit
- Armazenamento em banco de dados PostgreSQL
- Deploy full-stack no Render
- Gerenciamento moderno de dependências com **`uv`**
- Padrões profissionais com pre-commit hooks

## 🏗️ Arquitetura do Sistema

```text
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────────┐
│   Fontes de     │    │  Prefect Cloud  │    │   Banco de           │
│   Dados (API)   │────▶ (Orquestração)  │────▶   Dados (Postgres)  │
└─────────────────┘    └─────────────────┘    └──────────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │    Streamlit    │
                                              │   Dashboard     │
                                              └─────────────────┘
                                                        │
                                                        ▼
                                                 Usuário Final
```

## 🔄 Pipeline ETL

Os fluxos ETL são responsávesi por:

1. **Extração:** Coleta de dados das criptomoedas via API
2. **Trandformação:** Limpeza, padronização e estruturação
3. **Carga:** Inserção no banco de dados

Fluxos disponíveis:

- `flow.etl.py` -> Pipeline principal de ingestão
- `flow_ohlc.py` -> Processamento de dados OHLC (Open, High, Low, Close)

## 📊 Aplicação Streamlit

A aplicação web permitr:

- Visualizar dados das criptomoedas processados
- Acompanhar métricas e séries temporais
- Interagie com os dados de forma dinâmica

Executada via (Localmente):

```bash
streamlit run app.py
```

## 🗂️ Estrutura do Projeto

```text
ENG_FINOPSETL
│
├── flows/                    # Fluxos Prefect (ETL)
│   ├── flow_etl.py
│   └── flow_ohlc.py
│
├── image/                    # Imagens usadas na documentação
├── app.py                    # Aplicação Streamlit
├── prefect.yaml              # Configuração do deploy no Prefect Clould
├── pyproject.toml            # Configuração de dependências do projeto (UV)
├── requirements.txt          # Dependências usadas para o deploy no Prefect Cloud
├── .pre-commit-config.yaml   # Hooks de qualidade de código
└── README.md                 # Documentação
```

## 🚀 Deploy no Render

**Configuração do serviço Web:**

1. Build Command: **`uv sync`**
2. Start Command: **`streamlit run app`**

![ ](https://github.com/Prog-LucasAlves/ENG_FinOpsETL/blob/main/image/render.png?raw=true)

3. Python Version(Environment Variables): **`3.13.5`**
4. PostgreSQL na plataforma do Render(Environment Variables)
    - **External Database URL** do banco de dados criado na plataforma do Render

![ ](https://github.com/Prog-LucasAlves/ENG_FinOpsETL/blob/main/image/render_environment.png?raw=true)

Banco de dados:

- Criar PostrgreSQL no Render
- Usar a variável **Extrenal Database URL**

![ ](https://github.com/Prog-LucasAlves/ENG_FinOpsETL/blob/main/image/Render_postgresql.png?raw=true)

🔗 **Link do Deploy:** [https://eng-finopsetl.onrender.com/](https://eng-finopsetl.onrender.com/)

## ☁️ Orquestração com Prefect Cloud

O prefect é responsavel por:

- Agendamento dos fluxos
- Monitoramento de execuções
- Logs e retries automáticos

> [!IMPORTANT]
> Primeiro, crie/certifique-se de que seu arquivo `prefect.yaml' esta configurado corretamente.

Você pode gerar um modelo base:

```bash
prefect init
```

Deploy do fluxo:

```bash
prefect deploy
```

## 🛠️ Configuração do Ambiente Local

📋 Pré-requisitos

- Python 3.13+
- Git
- Conta no [Prefect Cloud](https://www.prefect.io/prefect/cloud)
- Conta no [Render](https://render.com/)

🔧 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/Prog-LucasAlves/ENG_FinOpsETL
cd ENG_FINOPSETL
```

2. Configure o ambiente virtual:

Instalar o **[UV](https://docs.astral.sh/uv/getting-started/installation/)**

```bash
uv init

uv venv
source .venv/bin/activate # Linux/MacOs
source .venv\Scripts\activate # Windows
```

3. Instale as dependências:

```bash
uv sync
```

## 🔐 Variáveis de Ambiente

Exemplo `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finance
DB_USER=postgres
DB_PASSWORD=senha
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/...
```

## 🧪 Qualidade de Código

O projeto utiliza:

- **Ruff** -> Linter
- **Pre-commit hooks** -> Padronização automática
- **Secrets baseline** -> Segurança

Executar manualmente:

```bash
pre-commit run --all-files
```

## 📄 Licença

Este projeto está sob a licença [MIT]().
