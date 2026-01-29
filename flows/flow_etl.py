from prefect import flow, task, variables
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


# https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&per_page=100
# https://docs.coingecko.com/v3.0.1/reference/coins-markets#coins-list-with-market-data


# Configurações Banco de Dados
DB_HOST = variables.get("dbhost")
DB_PORT = variables.get("dbport")
DB_NAME = variables.get("dbname")
DB_USER = variables.get("dbuser")
DB_PASSWORD = variables.get("dbpassword")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configurações da API
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Parâmetros da API
PARAMS = {
    "vs_currency": "brl",  # Moeda em Reais
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "24h,7d",
}


# Modelo Pydantic
class CryptoData(BaseModel):
    id: str = Field(..., description="ID da Moeda")
    symbol: str = Field(..., description="Símbolo da Moeda")
    name: str = Field(..., description="Nome da Moeda")
    image: Optional[str] = Field(None, description="URL da imagem da Moeda")
    current_price: float = Field(
        ...,
        description="Preço Atual da Moeda em Moeda Corrente",
    )
    market_cap: float = Field(..., description="Capitalização de Mercado da Moeda")
    market_cap_rank: Optional[int] = Field(
        None,
        description="Ranking das Moedas por Capitalização de Mercado",
    )
    collected_at: datetime


@task(
    name="ETL",
    retries=3,
    retry_delay_seconds=1,
    timeout_seconds=60,
    tags=["extract", "crypto"],
)
# Criar a tabela se não existir
@task
def create_table_if_not_exists():
    """Cria a tabela no banco de dados se ela não existir"""
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS crypto (
                    id VARCHAR(255),
                    symbol VARCHAR(255),
                    name VARCHAR(255),
                    image TEXT,
                    current_price NUMERIC,
                    market_cap NUMERIC,
                    market_cap_rank INTEGER,
                    collected_at TIMESTAMP WITH TIME ZONE
                )
                """),
            )
            conn.commit()
        print("✅ Tabela 'crypto' verificada/criada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        raise


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
    """Valida e transforma e os dados brutos em DataFrame estruturado"""
    if not raw_data:
        raise ValueError("Nenhum dado recebido da API")

    # Lista de colunas
    selected_columns = [
        "id",
        "symbol",
        "name",
        "image",
        "current_price",
        "market_cap",
        "market_cap_rank",
    ]

    # Cria o DataFrame
    df = pd.DataFrame(raw_data)

    # Selecionar apenas as colunas desejadas
    available_columns = [col for col in selected_columns if col in df.columns]
    df = df[available_columns]

    # Adicionar timestamp
    df["collected_at"] = datetime.now(timezone.utc)

    # validação Pydantic
    validated_data = []
    for _, row in df.iterrows():
        try:
            crypto = CryptoData(**row.to_dict())
            validated_data.append(crypto.dict())
        except Exception as e:
            print(f"❌ Erro de validação Pydantic para linha {row.to_dict()}: {e}")
            continue

    # Cria um novo DataFrame com os dados validados
    df_validated = pd.DataFrame(validated_data)

    print(f"📊 DataFrame transformado. Shape: {df.shape}")
    for _, row in df.head(3).iterrows():
        print(
            f"  {row.get('id', 'N/A')} - {row.get('symbol', 'N/A')} - {row.get('market_cap_rank', 'N/A')}",
        )
    return df_validated


@task
def load(df):
    """Carrega o DataFrame no banco de dados(Render)"""
    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect():
            print("🔗 Conexão com banco estabelecida")

        # Salvar os dados no banco de dados
        df.to_sql("crypto", engine, if_exists="append", index=False)
        print(f"💾 Dados salvos no banco. {len(df)} registros inseridos.")

        # Verificar a inserção dos dados
        result = pd.read_sql("SELECT COUNT(*) as total FROM crypto", engine)
        print(f"📈 Total de registros na tabela: {result['total'].iloc[0]}")

    except Exception as e:
        print(f"❌ Erro ao carregar os dados: {e}")
        raise


@flow(name="Fluxo ETL(Summary) de Criptomoedas", log_prints=True)
def crypto_etl():
    """Orquestrador principal do ETL"""
    print("🚀 Iniciando pipeline ETL(Summary) de criptomoedas...")

    create_table_if_not_exists()

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
