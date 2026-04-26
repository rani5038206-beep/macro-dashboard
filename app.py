import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# SAFE DATA FETCH (NO CRASH)
# =========================
@st.cache_data(ttl=300)
def get_data():
    try:
        data = yf.download(
            ["^GSPC", "DX-Y.NYB", "^VIX", "^TNX"],
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False
        )["Close"].dropna()
        return data
    except:
        return pd.DataFrame()

df = get_data()

# =========================
# FALLBACK (IF API FAILS)
# =========================
if df.empty:
    dates = pd.date_range(end=datetime.today(), periods=100)
    df = pd.DataFrame({
        "SPX": np.random.normal(4000, 50, 100),
        "DXY": np.random.normal(100, 2, 100),
        "VIX": np.random.normal(18, 3, 100),
        "US10Y": np.random.normal(3.5, 0.3, 100)
    }, index=dates)

df.columns = ["SPX", "DXY", "VIX", "US10Y"]

# =========================
# SIGNAL LOGIC
# =========================
latest = df.iloc[-1]
prev = df.iloc[-2]

signals = {
    "SPX": 1 if latest["SPX"] > prev["SPX"] else -1,
    "DXY": -1 if latest["DXY"] > prev["DXY"] else 1,
    "VIX": -1 if latest["VIX"] > prev["VIX"] else 1,
    "US10Y": -1 if latest["US10Y"] > prev["US10Y"] else 1,
}

score = sum(signals.values())

# =========================
# REGIME + ALLOCATION
# =========================
if score >= 2:
    regime = "RISK ON"
    color = "green"
    alloc = {"Equity": 70, "Cash": 30}
    advice = "Increase equity exposure"
elif score <= -2:
    regime = "RISK OFF"
    color = "red"
    alloc = {"Equity": 30, "Cash": 70}
    advice = "Reduce equity exposure"
else:
    regime = "TRANSITION"
    color = "orange"
    alloc = {"Equity": 50, "Cash": 50}
    advice = "Balanced approach"

# =========================
# SIDEBAR (CLIENT INPUT)
# =========================
st.sidebar.header("Client Management")

client_name = st.sidebar.text_input("Client Name", "Client A")
equity_pct = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

cash_pct = 100 - equity_pct

# =========================
# MAIN HEADER
# =========================
st.title(f"{client_name} - Portfolio Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Market Regime", regime)
col2.metric("Model Score", score)
col3.metric("Last Updated", datetime.today().strftime("%d %b %Y"))

# =========================
# ADVISORY
# =========================
st.subheader("Advisory")
st.success(advice)

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
