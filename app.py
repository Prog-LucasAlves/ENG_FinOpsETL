import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import warnings
import plotly.express as px
from datetime import datetime, timedelta
import os
import dotenv
import pytz
from prefect.settings import PREFECT_API_URL, PREFECT_API_KEY

warnings.filterwarnings("ignore")

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Criptomoedas",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
        margin-top: 1.5rem;
        margin-bottom: 0.1rem;
        font-weight: 600;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .crypto-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s;
        margin-bottom: 1rem;
    }
    .crypto-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stButton button {
        background-color: #3B82F6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #2563EB;
        color: white;
    }
    .info-box {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #93C5FD;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


class CrytoData:
    def __init__(self, db_url: str):
        """
        Inicializa a classe CrytoData

        Args:
            db_url (str): URL de conexão com o banco de dados
        """
        self.engine = create_engine(db_url)

    def get_latest_data(self) -> pd.DataFrame:
        """
        Obtém os dados mais recentes de cada moeda

        Returns:
            pd.DataFrame: DataFrame com os dados mais recentes
        """
        query = """
        WITH RankeData AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY id ORDER BY collected_at DESC) AS rn
            FROM crypto
        )
        SELECT id, symbol, name, image, current_price, market_cap, market_cap_rank, collected_at
        FROM RankeData
        WHERE rn =1
        ORDER BY market_cap_rank NULLS LAST, symbol
        """
        return pd.read_sql(query, self.engine)

    def get_historical_data(self, days: int = 7) -> pd.DataFrame:
        """
        Obtém os dados históricos de uma moeda específica

        Args:
            days (int): Número de dias de dados históricos

        Returns:
            pd.DataFrame: DataFrame com os dados históricos
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        query = """
        SELECT id, symbol, name, image, current_price, market_cap, market_cap_rank, collected_at
        FROM crypto
        WHERE collected_at >= %s
        ORDER BY collected_at DESC, market_cap_rank
        """
        return pd.read_sql(query, self.engine, params=(cutoff_date,))

    def get_top_cryptos(self, limit: int = 10) -> pd.DataFrame:
        """
        Obtém as top N criptomoedas por rank

        Args:
            limit (int): Número de moedas top a serem retornadas

        Returns:
            pd.DataFrame: DataFrame com as moedas top
        """
        query = """
        WITH RankedData AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY id ORDER BY collected_at DESC) AS rn
            FROM crypto
        )
        SELECT id, symbol, name, image, current_price, market_cap, market_cap_rank
        FROM RankedData
        WHERE rn = 1 AND market_cap_rank IS NOT NULL
        ORDER BY market_cap_rank
        LIMIT %s
        """
        return pd.read_sql(query, self.engine, params=(limit,))


def display_crypto_card(crypto: pd.Series, col):
    """
    Exibe um card individual para cada criptomorda

    Args:
        crypto (pd.Series): Dados da criptomoeda
        col: Coluna do Streamlit para exibição
    """
    with col:
        current_price_card = (
            f"{crypto['current_price']:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        market_cap_card = (
            f"{crypto['market_cap']:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        st.markdown(
            f"""
                    <div class="crypto-card">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            {f'<img src="{crypto["image"]}" width="50" height="50" style="border-radius: 50%; margin-right: 10px;">' if crypto.get("image") else ""}
                            <div>
                                <h4 style="margin: 0; color: #1E293B;">{crypto["name"]}</h4>
                                <p style="margin: 0; color: #64748B; font-size: 0.9rem;">{crypto["symbol"].upper()}</p>
                            </div>
                        </div>
                        {f'<p style="margin: 5px 0; color: #475569;"><strong>Rank:</strong> #{crypto["market_cap_rank"]}</p>' if pd.notna(crypto.get("market_cap_rank")) else ""}
                            <p style="margin: 5px 0; color: #475569;"><strong>ID:</strong> {crypto["id"]}</p>
                            <p style="margin: 5px 0; color: #475569;"><strong>Preço:</strong> R$ {current_price_card}</p>
                            <p style="margin: 5px 0; color: #475569;"><strong>Market Cap:</strong> R$ {market_cap_card}</p>
                    </div>
                        """,
            unsafe_allow_html=True,
        )


def main():
    """
    Configurações do banco de dados
    """
    dotenv.load_dotenv()
    DB_URL = os.getenv("DB_URL")
    crypto_data = CrytoData(DB_URL)

    # Barra lateral
    with st.sidebar:
        st.markdown(
            """
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <h1 style="color: #3B82F6; font-size: 7rem;">🪙​</h1>
                        <h2 style="color: #3898e7; font-size: 2rem;">Crypto Dashboard</h2>
                        <p style="color: #64748B;">Monitoramento em tempo real</p>
                    </div>
                    """,
            unsafe_allow_html=True,
        )

        # Filtros
        st.markdown("### 🔍 Filtros")

        view_mode = st.selectbox(
            "Modo de Visualização",
            ["Visão Geral", "Top 10", "Histórico Completo", "Moeda Específica"],
        )

        if view_mode == "Top 10":
            top_n = st.slider("Número de Moedas", 5, 50, 10)
        elif view_mode == "Histórico Completo":
            days_history = st.slider("Dias de Histórico", 1, 30, 7)
        elif view_mode == "Moeda Específica":
            latest_data = crypto_data.get_latest_data()
            crypto_options = latest_data["name"].tolist()
            selected_crypto = st.selectbox("Selecione a Criptomoeda", crypto_options)
            days_specific = st.slider("Período (dias)", 1, 90, 30)
            if selected_crypto:
                crypto_id = latest_data[latest_data["name"] == selected_crypto][
                    "id"
                ].iloc[0]

        st.markdown("---")

        latest_data = crypto_data.get_latest_data()

        ### Informações 1

        st.header("📢 Últimas Notícias")
        st.caption("Notícias em tempo atualizado - Fonte: Darqube")
        TOKEN = os.getenv("TOKEN")

        news_widget = f"""
            <iframe
                style="border: none; width:100%; height: 999px; border-radius: 10px;"
                data-widget-name="NewsWidget"
                src="https://widget.darqube.com/news-widget?token={TOKEN}"
                id="NewsWidget-teu68pe">
            </iframe>
            """

        # Incorporar o widget
        st.components.v1.html(news_widget, height=1000)

        st.markdown("---")

        ### Informações 2

        # Ajustar data de atualização
        latest_timestamp = latest_data["collected_at"].max()

        if latest_timestamp.tz is not None:
            brasilia_tz = pytz.timezone("America/Sao_Paulo")
            latest_brasilia = latest_timestamp.astimezone(brasilia_tz)
            formatted_date = latest_brasilia.strftime("%d/%m/%Y %H:%M:%S")
        else:
            formatted_date = latest_timestamp.strftime("%d/%m/%Y %H:%M:%S")

        # Criar Status Prefect Cloud
        try:
            # Verificar configurações
            api_url = PREFECT_API_URL.value()
            api_key = PREFECT_API_KEY.value() if PREFECT_API_KEY else None

            if api_url and api_key:
                if "prefect.cloud" in api_url:
                    etl_status = "✅ Conectado ao Prefect Cloud"
                else:
                    etl_status = "🔗 Conectado ao servidor local"
            else:
                etl_status = "⚙️ Configure PREFECT_API_URL e PREFECT_API_KEY"

        except Exception as e:
            etl_status = f"❌ Erro: {str(e)[:50]}"

        ### Criar Status do banco
        status = (
            "✅ Conectado ao PostgreSQL"
            if crypto_data is not None
            else "⏳ Carregando..."
        )

        st.markdown("### ℹ️ Informações")
        st.markdown(
            f"""
        <div class="info-box">
            <p style="color: #64748B;"><strong>Atualização:</strong> {formatted_date}</p>
            <p style="color: #64748B;"><strong>Fonte:</strong> CoinGecko API</p>
            <p style="color: #64748B;"><strong>ETL(Prefect Cloud):</strong> {etl_status}
            <p style="color: #64748B;"><strong> Render PostgreSQL:</strong> {status}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Conteúdo principal
    st.markdown(
        '<h1 class="main-header">📈 Dashboard de Criptomoedas</h1>',
        unsafe_allow_html=True,
    )

    try:
        if view_mode == "Visão Geral":
            display_overview(crypto_data)
        elif view_mode == "Top 10":
            display_top_n(crypto_data, top_n)
        elif view_mode == "Histórico Completo":
            display_historical(crypto_data, days_history)
        elif view_mode == "Moeda Específica":
            display_specific_crypto(crypto_data, crypto_id, days_specific)

    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Verifique a conexão com o banco de dados e tente novamente.")


def display_overview(crypto_data):
    """Exibe visão geral dos dados"""

    # Carregar dados
    latest_data = crypto_data.get_latest_data()

    if latest_data.empty:
        st.warning("Nenhum dado encontrado no banco de dados.")
        return

    # Métricas principais
    st.markdown(
        '<h2 class="sub-header">📊 Métricas Principais</h2>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        total_cryptos = len(latest_data)
        st.metric("Total de Criptomoedas", total_cryptos)

    with col2:
        average_price_crypto = latest_data["current_price"].mean(skipna=True)
        average_price_crypto = (
            f"R$ {average_price_crypto:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        st.metric("Média de Preço das 100 Maiores Criptomoedas", average_price_crypto)

    with col3:
        total_market_cap = latest_data["market_cap"].sum()
        total_market_cap = (
            f"R$ {total_market_cap:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        st.metric("Market Cap Total das 100 Maiores Criptomoedas", total_market_cap)

    st.markdown("---")

    ### Top 5 criptomoedas
    st.markdown(
        '<h2 class="sub-header">🏆 Top 5 Criptomoedas</h2>',
        unsafe_allow_html=True,
    )

    top_5 = latest_data.sort_values("market_cap_rank").head(5)

    cols = st.columns(5)
    for idx, (_, crypto) in enumerate(top_5.iterrows()):
        display_crypto_card(crypto, cols[idx])

    st.markdown("---")

    ### Tabela completa
    st.markdown(
        '<h2 class="sub-header">📋 Todas as Criptomoedas</h2>',
        unsafe_allow_html=True,
    )

    # Formatar DataFrame para exibição
    display_df = latest_data.copy()

    display_df["symbol"] = display_df["symbol"].str.upper()

    # Selecionar e ordenar colunas
    display_df = display_df[
        ["image", "name", "symbol", "market_cap_rank", "current_price", "market_cap"]
    ]

    def format_price(price):
        if pd.isna(price):
            return ""

        price_formatted = f"R$ {price:,.2f}"
        return price_formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    display_df["current_price"] = display_df["current_price"].apply(format_price)
    display_df["market_cap"] = display_df["market_cap"].apply(format_price)

    # Exibir tabela
    st.dataframe(
        display_df[5:],
        width="content",
        hide_index=True,
        height=1500,
        column_config={
            "image": st.column_config.ImageColumn("Logo", width="small"),
            "name": st.column_config.TextColumn("CryptoMoeda", width="medium"),
            "symbol": st.column_config.TextColumn("Símbolo", width="small"),
            "market_cap_rank": st.column_config.NumberColumn("Rank"),
            "current_price": st.column_config.TextColumn("Preço"),
            "market_cap": st.column_config.TextColumn("Market Cap"),
        },
    )

    # Gráfico de distribuição de ranks
    st.markdown("---")
    st.markdown(
        '<h2 class="sub-header">📈 Distribuição de Ranks</h2>',
        unsafe_allow_html=True,
    )

    fig = px.histogram(
        latest_data.dropna(subset=["market_cap_rank"]),
        x="market_cap_rank",
        nbins=20,
        title="Distribuição dos Ranks de Market Cap",
        labels={"market_cap_rank": "Rank", "count": "Quantidade de Moedas"},
        color_discrete_sequence=["#3B82F6"],
    )
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
    st.plotly_chart(fig, use_container_width=True)


def display_top_n(crypto_data, n):
    """Exibe top N criptomoedas"""

    top_cryptos = crypto_data.get_top_cryptos(n)

    if top_cryptos.empty:
        st.warning(f"Nenhum dado encontrado para as top {n} criptomoedas.")
        return

    st.markdown(
        f'<h2 class="sub-header">🏅 Top {n} Criptomoedas por Market Cap</h2>',
        unsafe_allow_html=True,
    )

    # Exibir cards em grid
    cols_per_row = 5
    rows = (len(top_cryptos) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            idx = row * cols_per_row + col_idx
            if idx < len(top_cryptos):
                display_crypto_card(top_cryptos.iloc[idx], cols[col_idx])

    st.markdown("---")

    # Gráfico de barras
    fig = px.bar(top_cryptos, x="symbol")

    fig.update_traces(texttemplate="#%{text}", textposition="outside")

    fig.update_layout(
        plot_bgcolor="white",
    )

    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabela Detalhada


def display_historical(crypto_data, days):
    """Exibe dados históricos"""

    historical_data = crypto_data.get_historical_data(days)

    if historical_data.empty:
        st.warning("Nenhum dado histórico encontrado.")
        return

    st.markdown(
        f'<h2 class="sub-header">📅 Histórico Completo ({days} dias)</h2>',
        unsafe_allow_html=True,
    )

    # Métricas
    unique_cryptos = historical_data["id"].nunique()
    total_records = len(historical_data)
    avg_updates = total_records / days if days > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Criptomoedas", unique_cryptos)
    col2.metric("Total de Registros", total_records)
    col3.metric("Média de Atualizações/Dia", f"{avg_updates:.1f}")

    st.markdown("---")

    # Gráfico de atualizações ao longo do tempo
    st.markdown(
        '<h3 class="sub-header">📊 Atualizações ao Longo do Tempo</h3>',
        unsafe_allow_html=True,
    )

    updates_by_day = (
        historical_data.groupby(historical_data["collected_at"].dt.date)
        .size()
        .reset_index(name="count")
    )

    fig = px.line(
        updates_by_day,
        x="collected_at",
        y="count",
        title=f"Atualizações por Dia (Últimos {days} dias)",
        markers=True,
        line_shape="spline",
    )

    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        height=400,
        xaxis_title="Data",
        yaxis_title="Número de Atualizações",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabela de dados históricos
    st.markdown(
        '<h3 class="sub-header">📋 Dados Históricos</h3>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_crypto = st.selectbox(
            "Filtrar por Moeda",
            ["Todas"] + historical_data["name"].unique().tolist(),
        )

    with col2:
        sort_by = st.selectbox(
            "Ordernar por",
            [
                "Data (Mais Recente)",
                "Data (Mais Antiga)",
                "Rank (Melhor)",
                "Rank (Pior)",
                "Preço(Maior)",
                "Preço(Menor)",
            ],
        )

    # Aplicar filtros
    filtered_data = historical_data.copy()
    if selected_crypto != "Todas":
        filtered_data = filtered_data[filtered_data["name"] == selected_crypto]

        def format_variation(value):
            if pd.isna(value) or value is None:
                return ""
            elif value > 0:
                return f"🟢 +{value:.2f}%"
            elif value < 0:
                return f"🔴 {value:.2f}%"
            else:
                return f"🟡 {value:.2f}%"

        # filtered_data["%_Preco_dia_anterior"] = ((filtered_data['current_price'] - filtered_data['current_price'].shift(-1)) / filtered_data['current_price'].shift(1)) * 100
        filtered_data["%_Preco_dia_anterior"] = (
            filtered_data["current_price"] / filtered_data["current_price"].shift(-1)
            - 1
        ) * 100
        filtered_data["%_Preco_dia_anterior"] = filtered_data[
            "%_Preco_dia_anterior"
        ].apply(format_variation)
    else:
        filtered_data["%_Preco_dia_anterior"] = 0

    # Ordenar dados
    if sort_by == "Data (Mais Recente)":
        filtered_data = filtered_data.sort_values("collected_at", ascending=False)
    elif sort_by == "Data (Mais Antiga)":
        filtered_data = filtered_data.sort_values("collected_at", ascending=True)
    elif sort_by == "Rank (Melhor)":
        filtered_data = filtered_data.sort_values("market_cap_rank", ascending=True)
    elif sort_by == "Rank (Pior)":
        filtered_data = filtered_data.sort_values("market_cap_rank", ascending=False)

    # Formatar dados para exibição
    display_df = filtered_data.copy()

    # Acertar data e horas utc -3
    brasilia_tz = pytz.timezone("America/Sao_Paulo")

    display_df["collected_at"] = (
        display_df["collected_at"]
        .dt.tz_convert(brasilia_tz)  # Converter timezone
        .dt.strftime("%d/%m/%Y %H:%M:%S")  # Formatar
    )
    display_df["symbol"] = display_df["symbol"].str.upper()
    display_df["current_price"] = display_df["current_price"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    display_df["market_cap"] = display_df["market_cap"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    # Exibir tabela
    st.dataframe(
        display_df[
            [
                "name",
                "symbol",
                "market_cap_rank",
                "current_price",
                "%_Preco_dia_anterior",
                "market_cap",
                "collected_at",
            ]
        ],
        hide_index=True,
        height=600,
        column_config={
            "name": st.column_config.TextColumn("Criptomoeda", width="large"),
            "symbol": st.column_config.TextColumn("Símbolo", width="small"),
            "market_cap_rank": st.column_config.NumberColumn("Rank", width="small"),
            "current_price": st.column_config.TextColumn("Preço", width="small"),
            "%_Preco_dia_anterior": st.column_config.TextColumn(
                "% Variação",
                width="small",
            ),
            "market_cap": st.column_config.TextColumn("Market Cap", width="small"),
            "collected_at": st.column_config.TextColumn("Atualizado Em", width="small"),
        },
    )

    # Opção para download
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"historico_crypto_{days}_dias.csv",
        mime="text/csv",
    )


def display_specific_crypto(crypto_data, crypto_id, days):
    """Exibe dados de uma crypto específica"""
    ...


if __name__ == "__main__":
    main()
