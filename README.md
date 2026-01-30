# 🚀 Sistema de ETL de CriptoMoedas  com Streamlit

![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Prefect](https://img.shields.io/badge/prefect-ETL%20Orchestration-2E77BC) ![Render](https://img.shields.io/badge/Render-Deployed-2E77BC) ![MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Índice
  - [📋 Sobre o Projeto](#-sobre-o-projeto)
  - [✨ Funcionalidades Principais](#-funcionalidades-principais)
  - [🏗️ Arquitetura do Sistema](#️-arquitetura-do-sistema)
  - [🔧 Estrutura do Projeto](#-estrutura-do-projeto)
  - [🚀 Deploy na Render](#-deploy-na-render)
  - [🛠️ Configuração do Ambiente Local](#️-configuração-do-ambiente-local)

## 📋 Sobre o Projeto

FINOPSETL é uma plataforma completa de engenharia de dados financeira que combina pipeline ETL orquestrado com Prefect Cloud e uma aplicação web interativa construída com Streamlit. O sistema é projetado para coletar, processar, visualizar e analisar dados financeiros de forma automatizada e escalável.

## ✨ Funcionalidades Principais

- Pipeline ETL Automatizado: Orquestração robusta com Prefect Cloud
- Dashboard Interativo: Visualizações em tempo real com Streamlit
- Deploy na Nuvem: Hospedagem full-stack no Render
- Banco de Dados: Armazenamento seguro e escalável
- Qualidade de Código: Padrões profissionais com pre-commit hooks
- Ambiente Virtual: Gerenciamento de dependências com **`uv`**

## 🏗️ Arquitetura do Sistema

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Fontes de     │    │  Prefect Cloud  │    │   Banco de      │
│   Dados         │────▶ (Orquestração)  │────▶   Dados        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐                                     │
│   Render        │                                     │
│   (Deploy)      │◀───────────────────────────────────┘
│                 │
│  ┌─────────────┐│
│  │  Streamlit  ││
│  │    App      ││
│  └─────────────┘│
└─────────────────┘
```

## 🔧 Estrutura do Projeto

...

## 🚀 Deploy na Render

**Configuração do Deploy**

1. Build Command: **`uv sync`**
2. Start Command: **`streamlit run app`**

![ ](https://github.com/Prog-LucasAlves/ENG_FinOpsETL/blob/main/image/render.png?raw=true)

3. Python Version(Environment Variables): **`3.13.5`**
4. PostgreSQL na plafaorma do Render(Environment Variables)
    - **External Database URL** do banco de dados criado na plataforma do Rende

![ ](https://github.com/Prog-LucasAlves/ENG_FinOpsETL/blob/main/image/render_environment.png?raw=true)

🔗 **Link do Deploy:** [https://eng-finopsetl.onrender.com/](https://eng-finopsetl.onrender.com/)

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

Informações de como instalar o **[UV](https://docs.astral.sh/uv/getting-started/installation/)**

```bash
uv init

uv venv

source .venv/bin/activate # Linux/MacOs

source .venv\Scripts\activate # Windows
```

3. Instale as dependências::

```bash
uv sync
```
