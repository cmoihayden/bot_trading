import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np

# Charger les tickers
assets_df = pd.read_csv("tickers_all.csv")
tickers = assets_df['Ticker'].dropna().unique().tolist()
ticker_names = dict(zip(assets_df['Ticker'], assets_df['Nom complet']))

# Fonction sécurisée pour float
def safe_float(val):
    try:
        return float(np.squeeze(val))
    except:
        return np.nan

# Fonction de style
def style_dataframe(df):
    def highlight(row):
        styles = [''] * len(row)
        if row.get('Score', 0) >= 80:
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
            styled = styled.map(colorize, subset=[col])
            styled = styled.format({col: lambda x: f"{x:.2f}".rstrip('0').rstrip('.')})
    styled = styled.format({'Nom': lambda x: f"**{x}**"})
    return styled

# Interface
st.set_page_config(page_title="SpideyCrypto", layout="wide")
st.title("🕷️ SpideyCrypto - Analyse des Actifs")
st.caption(f"Dernière analyse : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.button("🚀 Lancer l’analyse complète"):
    with st.spinner("Analyse en cours... Patientez pendant que l'on analyse les actifs..."):
        results = []
        failed = []

        for symbol in tickers:
            try:
                # Téléchargement des données avec des bougies de 4 heures et une période de 30 jours
                data = yf.download(symbol, period="30d", interval="4h", progress=False, threads=True, auto_adjust=False)
                if data.empty:
                    failed.append(symbol)
                    continue

                # Vérification des données de clôture
                close = data['Close'].dropna()
                
                if len(close) < 6:  # Seuil ajusté pour les bougies de 4 heures
                    failed.append(symbol)
                    continue

                # Calcul des variations et RSI
                delta = close.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

                # S'assurer que l'index -2, -8, -25 existe avant d'y accéder
                rsi_value = safe_float(rsi.iloc[-2]) if len(rsi) > 1 else np.nan
                volume = safe_float(data['Volume'].iloc[-2]) if len(data['Volume']) > 1 else np.nan
                volume_avg = safe_float(data['Volume'].rolling(24).mean().iloc[-2]) if len(data['Volume']) > 24 else np.nan

                # Vérification des valeurs
                if np.isnan(rsi_value) or np.isnan(volume_avg):
                    st.warning(f"Valeurs manquantes pour {symbol} (RSI: {rsi_value}, Volume: {volume}, Volume moyen: {volume_avg})")
                    failed.append(symbol)
                    continue

                # Calcul des pourcentages de changement
                pct_change_6h = ((close.iloc[-2] - close.iloc[-8]) / close.iloc[-8]) * 100 if len(close) > 8 else np.nan
                pct_change_24h = ((close.iloc[-2] - close.iloc[-25]) / close.iloc[-25]) * 100 if len(close) > 25 else np.nan
                pct_change_7d = ((close.iloc[-2] - close.iloc[0]) / close.iloc[0]) * 100 if len(close) > 1 else np.nan

                # Assurez-vous que ces valeurs sont des scalaires
                pct_change_6h = pct_change_6h.item() if isinstance(pct_change_6h, pd.Series) else pct_change_6h
                pct_change_24h = pct_change_24h.item() if isinstance(pct_change_24h, pd.Series) else pct_change_24h
                pct_change_7d = pct_change_7d.item() if isinstance(pct_change_7d, pd.Series) else pct_change_7d

                # Calcul du score
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

                # Enregistrement des résultats
                results.append({
                    'Nom': ticker_names.get(symbol, symbol),
                    'Actif': symbol,
                    'Changement (6h) (%)': round(pct_change_6h, 2),
                    'Changement (24h) (%)': round(pct_change_24h, 2),
                    'Changement (7j) (%)': round(pct_change_7d, 2),
                    'RSI': round(rsi_value, 2),
                    'Score': score
                })

            except Exception as e:
                st.warning(f"Erreur pour {symbol}: {str(e)}")
                failed.append(symbol)

        # Traitement des résultats
        df = pd.DataFrame(results)
        if not df.empty:
            df = df[df['Score'] > 0]
            df = df.sort_values(by='Score', ascending=False).head(100)
            st.dataframe(style_dataframe(df), use_container_width=True, hide_index=True)
        else:
            st.warning("❌ Aucun actif détecté.")

        # Affichage des statistiques
        st.caption(f"✅ Actifs analysés avec succès : {len(results)}")
        st.caption(f"❌ Actifs échoués : {len(failed)}")
