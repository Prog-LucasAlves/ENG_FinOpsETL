from prefect import flow, task, variables
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


# https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=brl&days=7

# Configurações Banco de Dados
DB_HOST = variables.get("dbhost")
DB_PORT = variables.get("dbport")
DB_NAME = variables.get("dbname")
DB_USER = variables.get("dbuser")
DB_PASSWORD = variables.get("dbpassword")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Pegar os IDs das Criptomoedas no banco de dados
...

COINS = ["bitcoin", "xrp"]


# Modelo Pydantic
class CryptoData(BaseModel):
    collected_at: datetime
    name: str
    open: float
    high: float
    low: float
    close: float


@task(
    name="ETL-OHLC",
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
                CREATE TABLE IF NOT EXISTS crypto_ohlc (
                    collected_at TIMESTAMP WITH TIME ZONE,
                    name VARCHAR(255),
                    open NUMERIC,
                    high NUMERIC,
                    low NUMERIC,
                    close NUMERIC
                )
                """),
            )
            conn.commit()
        print("✅ Tabela 'crypto_ohlc' verificada/criada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        raise


def extract():
    """Extrai dados da API do CoinGecko com os ids constante COIN"""
    for COIN in COINS:
        COINGECKO_URL = f"https://api.coingecko.com/api/v3/coins/{COIN}/ohlc"
        PARAMS = {"vs_currency": "brl", "days": 7}
        response = requests.get(COINGECKO_URL, params=PARAMS)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(
                data,
                columns=["collected_at", "name", "open", "high", "low", "close"],
            )
            df["collected_at"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["name"] = COIN
            yield df
        else:
            print(f"Erro na requisição para {COIN}: {response.status_code}")


def transform(raw_data):
    """Valida e transforma e os dados brutos em DataFrame estruturado"""
    if not raw_data:
        raise ValueError("Nenhum dado recebido da API")

    # Lista de colunas
    selected_columns = [
        "collected_at",
        "name",
        "open",
        "high",
        "low",
        "close",
    ]

    # Cria o DataFrame
    df = pd.DataFrame(raw_data)

    # Selecionar apenas as colunas desejadas
    available_columns = [col for col in selected_columns if col in df.columns]
    df = df[available_columns]

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
            f"  {row.get('name', 'N/A')} - {row.get('time', 'N/A')} - {row.get('open', 'N/A')}",
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
        df.to_sql("crypto_ohlc", engine, if_exists="append", index=False)
        print(f"💾 Dados salvos no banco. {len(df)} registros inseridos.")

        # Verificar a inserção dos dados
        result = pd.read_sql("SELECT COUNT(*) as total FROM crypto_ohlc", engine)
        print(f"📈 Total de registros na tabela: {result['total'].iloc[0]}")

    except Exception as e:
        print(f"❌ Erro ao carregar os dados: {e}")
        raise


@flow(name="Fluxo ETL(OHLC) de Criptomoedas", log_prints=True)
def crypto_etl():
    """Orquestrador secundário do ETL"""
    print("🚀 Iniciando pipeline ETL(OHLC) de criptomoedas...")
    print("💰 Moeda: BRL (Real Brasileiro)")

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
