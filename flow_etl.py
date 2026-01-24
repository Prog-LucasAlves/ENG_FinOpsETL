from prefect import flow, task
import requests
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Parâmetros da API
PARAMS = {
    "vs_currency": "brl",  # Moeda em Reais
    "ids": "bitcoin,ethereum,cardano,ripple,binancecoin,solana,dogecoin,polkadot,matic-network,stellar",  # Top 10 criptomoedas
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "24h,7d",
}


@task(
    name="ETL",
    retries=3,
    retry_delay_seconds=1,
    timeout_seconds=60,
    tags=["extract", "crypto"],
)
def extract():
    """Extrai dados da API do CoinGecko"""
    try:
        r = requests.get(COINGECKO_URL, params=PARAMS, timeout=10)
        r.raise_for_status()
        print(
            f"✅ Dados extraídos com sucesso. {len(r.json())} criptomoedas encontradas.",
        )
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na extração: {e}")
        raise


@task
def transform(raw_data):
    """Transforma os dados brutos em DataFrame estruturado"""
    if not raw_data:
        raise ValueError("Nenhum dado recebido da API")

    # Lista de colunas
    selected_columns = ["id", "symbol"]

    # Cria o DataFrame
    df = pd.DataFrame(raw_data)

    # Selecionar apenas as colunas desejadas
    available_columns = [col for col in selected_columns if col in df.columns]
    df = df[available_columns]

    # Adicionar timestamp
    df["collected_at"] = datetime.utcnow()

    # Renomear colunas para português
    column_mapping = {"id": "id_moeda", "symbol": "simbolo"}

    # Aplicar renomeação
    existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mapping)

    print(f"📊 DataFrame transformado. Shape: {df.shape}")
    print("💰 Banco de Dados:")
    for _, row in df.head(3).iterrows():
        print(f"  {row.get('id_moeda', 'N/A')} - {row.get('simbolo', 'N/A')}")
    return df


@task
def load(df):
    """Carrega o DataFrame no banco de dados(Render)"""
    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect():
            print(f"🔗 Conexão com banco estabelecida: {DB_URL.split('@')[-1]}")

        # Salvar os dados no banco de dados
        df.to_sql("crypto_qswl", engine, if_exists="append", index=False)
        print(f"💾 Dados salvos no banco. {len(df)} registros inseridos.")

        # Verificar a inserção dos dados
        result = pd.read_sql("SELECT COUNT(*) as total FROM crypto_quotes", engine)
        print(f"📈 Total de registros na tabela: {result['total'].iloc[0]}")

    except Exception as e:
        print(f"❌ Erro ao carregar os dados: {e}")
        raise


@flow(name="Fluxo ETL de Criptomoedas", log_prints=True)
def crypto_etl():
    """Orquestrador principal do ETL"""
    print("🚀 Iniciando pipeline ETL de criptomoedas...")
    print(f"🌐 API: {COINGECKO_URL}")
    print("💰 Moeda: BRL (Real Brasileiro)")

    # Extrair
    raw_data = extract()

    # Transformar
    df = transform(raw_data)

    # Carregar
    load(df)

    print("✅ Pipeline executado com sucesso!")
    return df


if __name__ == "__main__":
    # Executar o pipeline
    crypto_etl()
