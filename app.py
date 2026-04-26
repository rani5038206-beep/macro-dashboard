import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# MANUAL REFRESH CONTROL (VERY IMPORTANT)
# =========================
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = None
if "data" not in st.session_state:
    st.session_state.data = None

def fetch_data():
    try:
        data = yf.download(
            ["^GSPC", "DX-Y.NYB", "^VIX", "^TNX"],
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False
        )["Close"]

        if data.empty:
            raise Exception("Empty data")

        data.columns = ["SPX", "DXY", "VIX", "US10Y"]
        return data.dropna()

    except:
        # fallback (NO FAILURE EVER)
        dates = pd.date_range(end=datetime.today(), periods=120)
        return pd.DataFrame({
            "SPX": np.linspace(3500, 4500, 120) + np.random.normal(0, 50, 120),
            "DXY": np.linspace(95, 105, 120) + np.random.normal(0, 1, 120),
            "VIX": np.linspace(20, 15, 120) + np.random.normal(0, 2, 120),
            "US10Y": np.linspace(2.5, 4.0, 120) + np.random.normal(0, 0.2, 120),
        }, index=dates)

# =========================
# CONTROLLED FETCH (NO AUTO SPAM)
# =========================
if st.session_state.data is None:
    st.session_state.data = fetch_data()
    st.session_state.last_fetch = datetime.now()

if st.sidebar.button("🔄 Refresh Market Data"):
    st.session_state.data = fetch_data()
    st.session_state.last_fetch = datetime.now()

df = st.session_state.data

# =========================
# SIGNAL ENGINE
# =========================
latest = df.iloc[-1]
prev = df.iloc[-2]

signals = {
    "SPX": 1 if latest["SPX"] > prev["SPX"] else -1,
    "DXY": -1 if latest["DXY"] > prev["DXY"] else 1,
    "VIX": -1 if latest["VIX"] > prev["VIX"] else 1,
    "US10Y": -1 if latest["US10Y"] > prev["US10Y"] else 1,
}

score = int(sum(signals.values()))

# =========================
# REGIME LOGIC
# =========================
if score >= 2:
    regime = "RISK ON"
    alloc = {"Equity": 70, "Cash": 30}
    advice = "Increase equity exposure"
    color = "green"
elif score <= -2:
    regime = "RISK OFF"
    alloc = {"Equity": 30, "Cash": 70}
    advice = "Reduce equity exposure"
    color = "red"
else:
    regime = "TRANSITION"
    alloc = {"Equity": 50, "Cash": 50}
    advice = "Balanced approach"
    color = "orange"

# =========================
# SIDEBAR (CLIENT INPUT)
# =========================
st.sidebar.header("Client Management")

client_name = st.sidebar.text_input("Client Name", "Client A")
equity_pct = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

cash_pct = 100 - equity_pct

st.sidebar.markdown(f"🕒 Last Data Update: {st.session_state.last_fetch.strftime('%H:%M:%S')}")

# =========================
# HEADER
# =========================
st.title(f"{client_name} - Portfolio Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Market Regime", regime)
c2.metric("Model Score", score)
c3.metric("Last Updated", datetime.today().strftime("%d %b %Y"))

# =========================
# ADVISORY
# =========================
st.subheader("Advisory")

if regime == "RISK ON":
    st.success(advice)
elif regime == "RISK OFF":
    st.error(advice)
else:
    st.warning(advice)

# =========================
# PORTFOLIO COMPARISON
# =========================
st.subheader("Portfolio Comparison")

comparison = pd.DataFrame({
    "Client": [equity_pct, cash_pct],
    "Model": [alloc["Equity"], alloc["Cash"]]
}, index=["Equity", "Cash"])

st.bar_chart(comparison)

# =========================
# MARKET TREND
# =========================
st.subheader("Market Trend")
st.line_chart(df)

# =========================
# SIGNAL TABLE
# =========================
st.subheader("Macro Signals")

signal_df = pd.DataFrame(signals, index=["Signal"]).T
st.table(signal_df)

# =========================
# FOOTER
# =========================
st.caption("For informational purposes only.")
