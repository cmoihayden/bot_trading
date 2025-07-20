import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import time
import numpy as np

# Chargement des tickers depuis le fichier
assets_df = pd.read_csv("tickers_all.csv")
tickers = assets_df['Ticker'].dropna().unique().tolist()
ticker_names = dict(zip(assets_df['Ticker'], assets_df['Nom complet']))

# Fonction utilitaire sécurisée
def safe_float(val):
    try:
        return float(np.squeeze(val))
    except:
        return np.nan

# Fonction de style
def style_dataframe(df):
    def highlight(row):
        styles = [''] * len(row)
        if row.get('Score', 0) >= 70:
            for i in range(len(row)):
                styles[i] = 'color: gold; font-weight: bold'
        return styles

    def colorize(val):
        try:
            val = float(val)
            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
            return f'color: {color}'
        except:
            return ''

    styled = df.style.apply(highlight, axis=1)
    for col in ['Changement (6h) (%)', 'Changement (24h) (%)', 'Changement (7j) (%)']:
        if col in df.columns:
            styled = styled.applymap(colorize, subset=[col])
            styled = styled.format({col: lambda x: f"{x:.2f}".rstrip('0').rstrip('.')})
    styled = styled.format({
        'Nom': lambda x: f"**{x}**"
    })
    return styled

st.title("📊 Analyse des Actifs - SpideyCrypto")

if st.button("🚀 Lancer l’analyse complète"):
    with st.spinner("Analyse en cours, merci de patienter..."):
        results = []

        for symbol in tickers:
            try:
                data = yf.download(symbol, period="7d", interval="1h", progress=False)
                if data.empty or len(data) < 24:
                    continue

                close = data['Close'].dropna()
                if close.empty or len(close) < 24:
                    continue

                # RSI maison (14 périodes)
                delta = close.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

                rsi_value = safe_float(rsi.iloc[-1])
                volume = safe_float(data['Volume'].iloc[-1])
                volume_avg = safe_float(data['Volume'].rolling(24).mean().iloc[-1])

                if any(map(np.isnan, [rsi_value, volume, volume_avg])) or volume_avg == 0:
                    continue

                pct_change_6h = safe_float(((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100) if len(close) >= 6 else np.nan
                pct_change_24h = safe_float(((close.iloc[-1] - close.iloc[-24]) / close.iloc[-24]) * 100) if len(close) >= 24 else np.nan
                pct_change_7d = safe_float(((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100) if len(close) >= 48 else np.nan

                if any(map(np.isnan, [pct_change_6h, pct_change_24h, pct_change_7d])):
                    continue

                score = 0
                if pct_change_6h > 2:
                    score += 20
                if pct_change_24h > 5:
                    score += 20
                if pct_change_7d > 10:
                    score += 20
                if rsi_value < 70:
                    score += 20
                if volume > 1.5 * volume_avg:
                    score += 20

                results.append({
                    'Nom': ticker_names.get(symbol, symbol),
                    'Actif': symbol,
                    'Changement (6h) (%)': round(pct_change_6h, 4),
                    'Changement (24h) (%)': round(pct_change_24h, 4),
                    'Changement (7j) (%)': round(pct_change_7d, 4),
                    'RSI': round(rsi_value, 2),
                    'Score': score
                })

            except Exception:
                continue

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values(by='Score', ascending=False).head(100)
            st.dataframe(style_dataframe(df), use_container_width=True, hide_index=True)
        else:
            st.warning("❌ Aucun actif détecté.")
