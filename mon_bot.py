import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import ta
import requests
import time

# 🔐 Authentification simple par mot de passe
def check_password():
    def password_entered():
        if st.session_state["password"] == "spiderman84":
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.image("https://upload.wikimedia.org/wikipedia/en/0/0c/Spiderman50.jpg", width=200)
        st.title("🕸️ Bienvenue sur SpideyCrypto")
        st.markdown("**Analyse des cryptos et actions par ton alter ego arachnéen.**")
        st.text_input("🔐 Entrez le mot de passe :", type="password", on_change=password_entered, key="password")
        st.stop()

check_password()

# 🕸️ Animation de chargement
with st.spinner("🕷️ SpideyCrypto analyse le marché... Accroche-toi à ta toile 💥"):
    time.sleep(1.5)

# Configuration mobile-friendly
st.set_page_config(page_title="SpideyCrypto - Analyse technique", layout="centered")
st.title("📈 SpideyCrypto - Scanner d'opportunités")

# 🌗 Bouton de mode sombre
with st.sidebar:
    dark_mode = st.toggle("🌙 Mode sombre")

if dark_mode:
    st.markdown("""
        <style>
            body, .stApp { background-color: #111 !important; color: #eee !important; }
            .css-18e3th9, .css-1d391kg { background-color: #111 !important; }
        </style>
    """, unsafe_allow_html=True)

# 🔗 Bouton de partage
st.markdown("""
    <div style='text-align: center;'>
        <a href='https://spideycrypto.streamlit.app' target='_blank'>
            📲 <strong>Partager SpideyCrypto</strong>
        </a>
    </div>
    <br>
""", unsafe_allow_html=True)

st.markdown("""
Ce scanner affiche **tous les actifs analysés**, même sans signal fort.

- 📈 **Changement (6h, 24h, 7j)** : variations sur différentes périodes  
- 🚀 **Potentiel (%)** : marge jusqu'au plus haut des 7 derniers jours  
- 🟨 **Surbrillance jaune** : actif avec **fort potentiel** (Score ≥ 70)
""")

NEWS_API_KEY = st.secrets["api"]["newsdata"]

choix_type = st.selectbox("🔽 Type d’actifs à scanner :", ["Tous", "Actions uniquement", "Cryptos uniquement"])

if st.button("🔍 Scanner maintenant"):
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD', 'INTC', 'CRM', 'TSLA', 'META', 'AMZN', 'ORCL', 'IBM', 'SHOP',
              'PFE', 'MRNA', 'JNJ', 'BMY', 'REGN', 'GILD', 'LLY', 'AZN', 'VRTX', 'SNY', 'BIIB',
              'XOM', 'CVX', 'COP', 'SLB', 'BP', 'TOT', 'ENB', 'EQNR',
              'F', 'GM', 'TM', 'HMC', 'RIVN', 'LCID', 'STLA', 'VWAGY',
              'NFLX', 'ROKU', 'SPOT', 'BIDU', 'UBER', 'LYFT',
              'LVMUY', 'CPRI', 'TPR', 'RL', 'NKE', 'ADIDAS', 'PVH']

    cryptos = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOT-USD', 'MATIC-USD', 'AVAX-USD', 'ADA-USD', 'DOGE-USD', 'BNB-USD']

    if choix_type == "Actions uniquement":
        assets = stocks
    elif choix_type == "Cryptos uniquement":
        assets = cryptos
    else:
        assets = stocks + cryptos

    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=7)
    results = []

    with st.spinner("📡 Analyse en cours..."):
        for symbol in assets:
            data = yf.download(symbol, start=start, end=end, interval="1h", progress=False, auto_adjust=True)
            if data.empty or len(data) < 25:
                continue

            try:
                close_series = data["Close"]
                if isinstance(close_series, pd.DataFrame):
                    close_series = close_series.squeeze()

                rsi_series = ta.momentum.RSIIndicator(close_series).rsi()
                current_rsi = float(rsi_series.iloc[-1])

                data['volume_ma20'] = data['Volume'].rolling(window=20).mean()
                last_close = float(data['Close'].iloc[-1])
                close_6h = float(data['Close'].iloc[-6])
                close_24h = float(data['Close'].iloc[-24])
                close_start = float(data['Close'].iloc[0])

                pct_6h = ((last_close - close_6h) / close_6h) * 100
                pct_24h = ((last_close - close_24h) / close_24h) * 100
                pct_7d = ((last_close - close_start) / close_start) * 100

                volume = float(data['Volume'].iloc[-1])
                volume_avg = float(data['volume_ma20'].iloc[-1])
                volume_ratio = volume / volume_avg if volume_avg != 0 else 0

                highest = float(data['Close'].max())
                potentiel_pct = max(0, ((highest - last_close) / last_close) * 100)

                score = 0
                if pct_6h >= 30: score += 40
                elif pct_6h >= 15: score += 30
                elif pct_6h >= 5: score += 20
                elif pct_6h > 0: score += 10

                if volume_ratio >= 2: score += 30
                elif volume_ratio >= 1.5: score += 20
                elif volume_ratio >= 1.2: score += 10

                if 45 <= current_rsi <= 55: score += 30
                elif 40 <= current_rsi <= 60: score += 20
                elif 35 <= current_rsi <= 65: score += 10

                results.append({
                    'Actif': symbol,
                    'Cours': round(last_close, 2),
                    'Changement (6h) (%)': round(pct_6h, 2),
                    'Changement (24h) (%)': round(pct_24h, 2),
                    'Changement (7j) (%)': round(pct_7d, 2),
                    'RSI': round(current_rsi, 2),
                    'Volume xMM': round(volume_ratio, 2),
                    'Potentiel (%)': round(potentiel_pct, 2),
                    'Score': score
                })

            except Exception as e:
                st.error(f"⚠️ Erreur sur {symbol} : {e}")
                continue

    df = pd.DataFrame(results)

    if df.empty or 'Score' not in df.columns:
        st.warning("❌ Aucun actif détecté.")
        st.write("🔎 Données brutes :", results)
    else:
        df = df.sort_values(by='Score', ascending=False)
        st.success(f"✅ {len(df)} actifs analysés.")

        def highlight_high_score(row):
            if row['Score'] >= 70:
                return ['background-color: #fff3b0'] * len(row)
            return [''] * len(row)

        styled_df = df.style.apply(highlight_high_score, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        st.download_button("📥 Exporter en CSV", data=df.to_csv(index=False), file_name="resultats.csv", mime="text/csv")

        # 📰 Actualités via Newsdata.io
        st.subheader("📰 Actualités associées (Newsdata.io)")
        for _, row in df.iterrows():
            if row['Score'] < 60:
                continue
            symbole = row['Actif']
            st.markdown(f"**🧠 {symbole}**")
            url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={symbole}&language=fr"
            try:
                r = requests.get(url)
                data = r.json()
                articles = data.get("results", [])
                if not articles:
                    st.markdown("_Aucune actualité trouvée._")
                    continue
                for article in articles[:3]:
                    titre = article.get("title")
                    lien = article.get("link")
                    if titre and lien:
                        st.markdown(f"- [{titre}]({lien})")
            except Exception as e:
                st.markdown(f"_⚠️ Erreur actualité : {e}_")
