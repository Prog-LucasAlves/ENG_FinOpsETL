from prefect import flow, task, variables
from prefect.tasks import task_input_hash
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
import time
import pytz

load_dotenv()

# https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=brl&days=7

# Configurações Banco de Dados
DB_HOST = variables.get("dbhost")
DB_PORT = variables.get("dbport")
DB_NAME = variables.get("dbname")
DB_USER = variables.get("dbuser")
DB_PASSWORD = variables.get("dbpassword")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


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
    retry_delay_seconds=30,
    timeout_seconds=1800,
    tags=["extract", "crypto"],
)
@task
def create_table_if_not_exists():
    """Cria a tabela no banco de dados se ela não existir"""
    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect() as conn:
            # Criar tabela se não existir
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


@task
def get_id_coins() -> List[str]:
    """Pega os IDs das criptomoedas no banco de dados"""
    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect() as conn:
            # Query para pegar os IDs unicos das criptomoedas com market cap rank < 50
            query = text("SELECT DISTINCT id FROM crypto WHERE market_cap_rank < 50 ")
            result = conn.execute(query)
            coins_ids = [row[0] for row in result]

            # Tocar '-' por '_'
            coins_ids = [coin.replace("-", "_") for coin in coins_ids]

            print(f"🔍 IDs das criptomoedas: {coins_ids}")
            return coins_ids
    except Exception as e:
        print(f"❌ Erro ao pegar IDs das criptomoedas: {e}")
        raise


@task(
    timeout_seconds=1800,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(minutes=10),
)
def extract():
    """Extrai dados da API do CoinGecko com os ids constante COIN"""
    all_data = []

    COINS = get_id_coins()
    total_coins = len(COINS)
    delay_between_calls = 6

    KEY = variables.get("key")

    # Iterar sobre cada moeda e buscar os dados OHLC
    for i, COIN in enumerate(COINS, 1):
        try:
            COINGECKO_URL = f"https://api.coingecko.com/api/v3/coins/{COIN}/ohlc"
            PARAMS = {"vs_currency": "brl", "days": 7, "x_cg_demo_api_key": KEY}
            HEADERS = {
                "User-Agent": "Mozilla/5.0 (compatible; YourApp/1.0)",
                "Accept": "application/json",
            }
            session = requests.Session()
            response = session.get(
                COINGECKO_URL,
                params=PARAMS,
                headers=HEADERS,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()

                # Adicionar dados à lista all_data
                for item in data:
                    timestamp_ms = item[0]
                    open_price = item[1]
                    high_price = item[2]
                    low_price = item[3]
                    close_price = item[4]

                    collected_at = datetime.fromtimestamp(timestamp_ms / 1000.0)
                    collected_at = collected_at.replace(tzinfo=pytz.UTC)

                    # Adiciona os dados à lista
                    all_data.append(
                        {
                            "collected_at": collected_at,
                            "name": COIN,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "close": close_price,
                        },
                    )
                print(f"✅ [{i}/{total_coins}] {COIN}: {len(data)} registros")

            elif response.status_code == 429:
                # Se receber 429, aguarda e tenta novamente
                print(f"⚠️  {COIN}: Limite de requisições atingido. Aguardando...")
                time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
                continue

            elif response.status_code == 404:
                print(f"⚠️  {COIN} não encontrado (404)")
                continue

            else:
                print(f"❌ Erro {response.status_code} para {COIN}")

        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout para {COIN}. Continuando...")
            continue

        except Exception as e:
            print(f"⚠️  Erro inesperado em {COIN}: {str(e)}")
            continue

        if i < total_coins:
            time.sleep(delay_between_calls)

    print(f"✅ Total: {len(all_data)} registros de {len(all_data)} moedas")
    return all_data


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
            f"  {row.get('name', 'N/A')} - {row.get('collected_at', 'N/A')} - {row.get('open', 'N/A')}",
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


@task
def delete_duplicated_data():
    """Elimina dados duplicados na tabela crypto_ohlc"""
    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect() as conn:
            # Eliminar dados duplicados
            query = text("""
                DELETE FROM crypto_ohlc a
                WHERE a.ctid <> (
                    SELECT min(b.ctid)
                    FROM crypto_ohlc b
                    WHERE a.name = b.name
                    AND a.collected_at = b.collected_at
                )
            """)
            conn.execute(query)
            conn.commit()
            print("✅ Dados duplicados eliminados com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao eliminar dados duplicados: {e}")
        raise


@task
def create_view_per_coin():
    """Cria uma view para cada moeda na tabela crypto_ohlc"""
    COINS = get_id_coins()

    try:
        engine = create_engine(DB_URL)

        # Verifica conexão com o banco de dados
        with engine.connect() as conn:
            for coin in COINS:
                view_name = f"crypto_ohlc_{coin}"

                # Criar uma view para cada moeda
                query = text(f"""
                    CREATE OR REPLACE VIEW {view_name} AS
                    SELECT * FROM crypto_ohlc WHERE name = '{coin}'
                    AND collected_at LIKE '%01:00:00.000%'
                """)
                conn.execute(query)
                conn.commit()
                print(f"✅ View '{view_name}' criada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao criar views: {e}")
        raise


@flow(name="Fluxo ETL(OHLC) de Criptomoedas", log_prints=True)
def crypto_etl():
    """Orquestrador secundário do ETL"""
    print("🚀 Iniciando pipeline ETL(OHLC) de criptomoedas...")
    print("💰 Moeda: BRL (Real Brasileiro)")

    # Cria a tabela se ela não existir
    create_table_if_not_exists()

    # Extrai dos dados da API
    raw_data = extract()

    # Transformar os dados
    df = transform(raw_data)

    # Carregar os dados no banco de dados
    load(df)

    # Eliminar dados duplicados
    delete_duplicated_data()

    # Criar views por coin
    create_view_per_coin()

    print("✅ Pipeline executado com sucesso!")
    return df


if __name__ == "__main__":
    # Executar o pipeline
    crypto_etl()
