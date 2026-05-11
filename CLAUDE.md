# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app runs at `http://localhost:8501`. Streamlit hot-reloads on file save — no restart needed for most changes.

## Architecture

Single-file Streamlit app (`app.py`) that fetches, filters, and visualizes Brazilian stock data for 2025.

**Data flow:**
1. `carregar_dados()` — downloads all tickers from Yahoo Finance via `yfinance`, cached for 1 hour with `@st.cache_data(ttl=3600)`
2. `filtrar_periodo()` — slices the cached DataFrame by month range selected in the sidebar
3. Each `grafico_*()` function receives the filtered slice and returns a Plotly figure

**Key constants at the top of `app.py`:**
- `ACOES` — maps display name → Yahoo Finance ticker (e.g. `"VALE3.SA"`)
- `CORES` — maps display name → hex color used consistently across all charts
- `MESES` — maps Portuguese month names → integers for date filtering

**Chart functions:**
- `grafico_cotacao` — closing price line chart (R$)
- `grafico_performance` — normalized cumulative return (base 100 at period start); skips empty series after `dropna()`
- `grafico_volume` — grouped bar chart of daily volume
- `grafico_candlestick` — OHLC chart; uses `df.xs(ticker, axis=1, level=1)` to slice the raw MultiIndex DataFrame
- `grafico_retorno_mensal` — heatmap of monthly % returns via `resample("ME")`
- `tabela_estatisticas` — summary table with total return, annualized volatility (`std * sqrt(252)`), max/min prices and daily moves

**yfinance DataFrame structure:** `yf.download()` with multiple tickers returns a MultiIndex DataFrame `(price_type, ticker)`. `df["Close"]` gives a flat DataFrame with ticker symbols as columns.

**Cache:** The sidebar has a "Limpar cache e recarregar dados" button that calls `st.cache_data.clear()` + `st.rerun()`. Use this if a ticker shows no data (stale cache from a failed download).

## GitHub

Remote: `https://github.com/crisgmich-droid/Aprendendo-programa-o.git` (branch `main`)

```bash
# Push manual
git add .
git commit -m "mensagem"
git push
```

**Auto-push após cada commit:** um hook `post-commit` em `.git/hooks/post-commit` executa `git push` automaticamente sempre que um commit é feito.

```bash
# Criar o hook (executar uma vez)
echo '#!/bin/sh' > .git/hooks/post-commit
echo 'git push' >> .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

Se o push automático falhar (ex: conflito), rode `git push` manualmente para resolver.
