import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(page_title="Análise de Ações 2025", layout="wide", page_icon="📈")

ACOES = {
    "Petrobras (PETR4)": "PETR4.SA",
    "Itaú (ITUB4)": "ITUB4.SA",
    "Vale (VALE3)": "VALE3.SA",
}

CORES = {
    "Petrobras (PETR4)": "#009C3B",
    "Itaú (ITUB4)": "#003087",
    "Vale (VALE3)": "#E87722",
}

MESES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}


@st.cache_data(ttl=3600)
def carregar_dados():
    tickers = list(ACOES.values())
    df = yf.download(tickers, start="2025-01-01", end="2025-12-31", auto_adjust=True)
    return df


def filtrar_periodo(df, mes_inicio, mes_fim):
    inicio = pd.Timestamp(f"2025-{mes_inicio:02d}-01")
    fim = pd.Timestamp(f"2025-{mes_fim:02d}-01") + pd.offsets.MonthEnd(0)
    return df[(df.index >= inicio) & (df.index <= fim)]


def grafico_cotacao(fechamento, acoes_sel):
    fig = go.Figure()
    for nome, ticker in ACOES.items():
        if nome in acoes_sel:
            fig.add_trace(go.Scatter(
                x=fechamento.index,
                y=fechamento[ticker],
                name=nome,
                line=dict(color=CORES[nome], width=2),
                hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:.2f}<extra>" + nome + "</extra>",
            ))
    fig.update_layout(
        title="Cotação Histórica — Preço de Fechamento (R$)",
        xaxis_title="Data",
        yaxis_title="Preço (R$)",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
        height=420,
    )
    return fig


def grafico_performance(fechamento, acoes_sel):
    fig = go.Figure()
    for nome, ticker in ACOES.items():
        if nome in acoes_sel:
            serie = fechamento[ticker].dropna()
            if serie.empty:
                continue
            normalizada = (serie / serie.iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=normalizada.index,
                y=normalizada,
                name=nome,
                line=dict(color=CORES[nome], width=2),
                hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f}<extra>" + nome + "</extra>",
            ))
    fig.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Base 100")
    fig.update_layout(
        title="Performance Acumulada (base 100 no início do período)",
        xaxis_title="Data",
        yaxis_title="Índice (base 100)",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
        height=420,
    )
    return fig


def grafico_volume(volume, acoes_sel):
    nomes_sel = [n for n in acoes_sel]
    tickers_sel = [ACOES[n] for n in nomes_sel]
    vol_filtrado = volume[tickers_sel].copy()
    vol_filtrado.columns = nomes_sel

    fig = go.Figure()
    for nome in nomes_sel:
        fig.add_trace(go.Bar(
            x=vol_filtrado.index,
            y=vol_filtrado[nome],
            name=nome,
            marker_color=CORES[nome],
            opacity=0.8,
        ))
    fig.update_layout(
        title="Volume de Negociação Diário",
        xaxis_title="Data",
        yaxis_title="Volume (ações negociadas)",
        barmode="group",
        legend=dict(orientation="h", y=-0.15),
        height=380,
    )
    return fig


def grafico_candlestick(df_raw, acao_nome):
    ticker = ACOES[acao_nome]
    ohlc = df_raw.xs(ticker, axis=1, level=1) if isinstance(df_raw.columns, pd.MultiIndex) else df_raw
    fig = go.Figure(go.Candlestick(
        x=ohlc.index,
        open=ohlc["Open"],
        high=ohlc["High"],
        low=ohlc["Low"],
        close=ohlc["Close"],
        name=acao_nome,
        increasing_line_color="#2ecc71",
        decreasing_line_color="#e74c3c",
    ))
    fig.update_layout(
        title=f"Candlestick — {acao_nome}",
        xaxis_title="Data",
        yaxis_title="Preço (R$)",
        xaxis_rangeslider_visible=False,
        height=420,
    )
    return fig


def grafico_retorno_mensal(fechamento, acoes_sel):
    retornos = {}
    for nome, ticker in ACOES.items():
        if nome in acoes_sel:
            serie = fechamento[ticker].dropna()
            mensal = serie.resample("ME").last().pct_change() * 100
            retornos[nome] = mensal

    df_ret = pd.DataFrame(retornos)
    df_ret.index = df_ret.index.strftime("%b/%Y")
    df_ret = df_ret.dropna(how="all")

    fig = px.imshow(
        df_ret.T,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".1f",
        aspect="auto",
        title="Retorno Mensal por Ação (%)",
        labels=dict(x="Mês", y="Ação", color="Retorno (%)"),
    )
    fig.update_layout(height=300)
    return fig


def tabela_estatisticas(fechamento, acoes_sel):
    rows = []
    for nome, ticker in ACOES.items():
        if nome in acoes_sel:
            serie = fechamento[ticker].dropna()
            if len(serie) < 2:
                continue
            retorno_total = (serie.iloc[-1] / serie.iloc[0] - 1) * 100
            retorno_diario = serie.pct_change().dropna()
            volatilidade = retorno_diario.std() * (252 ** 0.5) * 100
            rows.append({
                "Ação": nome,
                "Preço Inicial (R$)": f"{serie.iloc[0]:.2f}",
                "Preço Final (R$)": f"{serie.iloc[-1]:.2f}",
                "Retorno Total (%)": f"{retorno_total:+.2f}%",
                "Volatilidade Anual (%)": f"{volatilidade:.2f}%",
                "Máximo (R$)": f"{serie.max():.2f}",
                "Mínimo (R$)": f"{serie.min():.2f}",
                "Maior Alta Diária (%)": f"{retorno_diario.max() * 100:+.2f}%",
                "Maior Queda Diária (%)": f"{retorno_diario.min() * 100:+.2f}%",
            })
    return pd.DataFrame(rows).set_index("Ação")


# ─── Layout ───────────────────────────────────────────────────────────────────

st.title("📈 Análise de Ações Brasileiras — 2025")
st.caption("Petrobras (PETR4) · Itaú (ITUB4) · Vale (VALE3)")

with st.sidebar:
    st.header("Filtros")
    acoes_sel = st.multiselect(
        "Ações",
        options=list(ACOES.keys()),
        default=list(ACOES.keys()),
    )
    meses_nomes = list(MESES.keys())
    mes_inicio_nome = st.selectbox("Mês de início", meses_nomes, index=0)
    mes_fim_nome = st.selectbox("Mês de fim", meses_nomes, index=len(meses_nomes) - 1)
    st.divider()
    acao_candle = st.selectbox("Ação para Candlestick", list(ACOES.keys()))
    st.divider()
    st.info("Dados fornecidos pelo Yahoo Finance via yfinance.")
    if st.button("Limpar cache e recarregar dados"):
        st.cache_data.clear()
        st.rerun()

if not acoes_sel:
    st.warning("Selecione ao menos uma ação na barra lateral.")
    st.stop()

mes_inicio = MESES[mes_inicio_nome]
mes_fim = MESES[mes_fim_nome]
if mes_inicio > mes_fim:
    st.error("O mês de início não pode ser posterior ao mês de fim.")
    st.stop()

with st.spinner("Carregando dados do Yahoo Finance..."):
    df_raw = carregar_dados()

fechamento_raw = df_raw["Close"] if "Close" in df_raw.columns.get_level_values(0) else df_raw
volume_raw = df_raw["Volume"] if "Volume" in df_raw.columns.get_level_values(0) else None

fechamento = filtrar_periodo(fechamento_raw, mes_inicio, mes_fim)
volume = filtrar_periodo(volume_raw, mes_inicio, mes_fim) if volume_raw is not None else None

# Seção 1 — Cotação + Performance
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(grafico_cotacao(fechamento, acoes_sel), use_container_width=True)
with col2:
    st.plotly_chart(grafico_performance(fechamento, acoes_sel), use_container_width=True)

# Seção 2 — Volume + Candlestick
col3, col4 = st.columns(2)
with col3:
    if volume is not None:
        tickers_sel = [ACOES[n] for n in acoes_sel if ACOES[n] in volume.columns]
        if tickers_sel:
            st.plotly_chart(grafico_volume(volume[[ACOES[n] for n in acoes_sel]], acoes_sel), use_container_width=True)
with col4:
    df_candle = filtrar_periodo(df_raw, mes_inicio, mes_fim)
    st.plotly_chart(grafico_candlestick(df_candle, acao_candle), use_container_width=True)

# Seção 3 — Retorno mensal
st.plotly_chart(grafico_retorno_mensal(fechamento_raw, acoes_sel), use_container_width=True)

# Seção 4 — Estatísticas
st.subheader("📊 Estatísticas do Período")
stats = tabela_estatisticas(fechamento, acoes_sel)
st.dataframe(stats, use_container_width=True)
