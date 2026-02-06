from sqlalchemy import create_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

# Configurações Banco de Dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)


engine = get_engine()


def create_tables():
    with engine.connect() as conn:
        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS crypto_data (
            id VARCHAR PRIMARY KEY,
            symbol VARCHAR,
            name VARCHAR,
            image VARCHAR,
            current_price FLOAT,
            market_cap FLOAT,
            market_cap_rank INT,
            collected_at TIMESTAMP
        );
        """),
        )
        conn.commit()

        conn.execute(
            text("""
        CREATE TABLE IF NOT EXISTS crypto_ohlc (
            id SERIAL PRIMARY KEY,
            collected_at TIMESTAMP,
            name VARCHAR,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT
        );
        """),
        )
        conn.commit()


if __name__ == "__main__":
    create_tables()
