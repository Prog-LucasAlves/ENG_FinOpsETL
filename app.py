from flask import Flask
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


db_path = r"../prefect/flows/marketpipe.db"


# String de conexão SQLite correta
engine = create_engine(f"sqlite:///{db_path}")


TEMPLATE = """
<h2>📊 Histórico de Preços - PETR4</h2>
{{ graph | safe }}
"""


@app.route("/")
def index():
    df = pd.read_sql(
        """
        SELECT currency
        FROM stock_quotes

        """,
        engine,
    )
    print(df)
