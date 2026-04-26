import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Client Dashboard", layout="wide")

# ---------------------------
# LOAD DATA (ROBUST)
# ---------------------------
@st.cache_data(ttl=3600)
def load_data():
    tickers = {
        "SPX": "^GSPC",
        "DXY": "DX-Y.NYB",
        "VIX": "^VIX",
        "US10Y": "^TNX"
    }

    data = {}

    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if not df.empty:
                data[name] = df["Close"]
        except:
            pass

    if len(data) == 0:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    return df.dropna()


df = load_data()

if df is None:
    st.error("❌ Data not loading. Try again later.")
    st.stop()

# ---------------------------
# SIGNAL ENGINE
# ---------------------------
weekly = df.resample("W").last()

for col in weekly.columns:
    weekly[f"{col}_S"] = np.where(
        weekly[col] > weekly[col].rolling(20).mean(), 1, -1
    )

latest = weekly.iloc[-1]

score = (
    latest["SPX_S"]
    - latest["DXY_S"]
    - latest["VIX_S"]
    - latest["US10Y_S"]
)

# ---------------------------
# REGIME LOGIC
# ---------------------------
if score >= 2:
    regime = "RISK ON"
    color = "🟢"
    allocation = {"Equity": 80, "Cash": 20}
    message = "Markets are supportive. Increasing equity exposure is recommended."
    reason = "Strong equity trend + low volatility + weak dollar"
elif score <= -2:
    regime = "RISK OFF"
    color = "🔴"
    allocation = {"Equity": 40, "Cash": 60}
    message = "Risk is elevated. Reduce equity exposure."
    reason = "Rising volatility + strong dollar + weakening equity trend"
else:
    regime = "TRANSITION"
    color = "🟡"
    allocation = {"Equity": 60, "Cash": 40}
    message = "Mixed signals. Maintain balanced allocation."
    reason = "Conflicting macro indicators"

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.header("👤 Client Portfolio")

equity = st.sidebar.slider("Equity %", 0, 100, 60)
cash = 100 - equity

portfolio_value = st.sidebar.number_input(
    "Portfolio Value (₹)", value=1000000
)

# ---------------------------
# HEADER
# ---------------------------
st.title("📊 Caring Click - Client Dashboard")

st.markdown("### 📌 Market Snapshot")

col1, col2, col3 = st.columns(3)

col1.metric("Market Regime", f"{color} {regime}")
col2.metric("Model Score", f"{score:.1f}")
col3.metric("Last Updated", df.index[-1].strftime("%d %b %Y"))

# ---------------------------
# ADVISORY BLOCK (STRONG)
# ---------------------------
st.markdown("### 📢 Advisory Decision")

if "Reduce" in message:
    st.error(f"🚨 {message}")
elif "Increasing" in message:
    st.success(f"🚀 {message}")
else:
    st.warning(f"⚖️ {message}")

st.markdown(f"**Why? → {reason}**")

# ---------------------------
# PORTFOLIO COMPARISON
# ---------------------------
st.markdown("### ⚖️ Portfolio Comparison")

client_alloc = {"Equity": equity, "Cash": cash}
model_alloc = allocation

comparison = pd.DataFrame({
    "Client": client_alloc,
    "Model": model_alloc
})

st.bar_chart(comparison.T)

# ---------------------------
# ACTION ENGINE
# ---------------------------
st.markdown("### 🚨 Required Action")

diff = model_alloc["Equity"] - equity

if diff > 10:
    action = f"Increase Equity by {diff}%"
elif diff < -10:
    action = f"Reduce Equity by {abs(diff)}%"
else:
    action = "No major change required"

if "Reduce" in action:
    st.error(f"🚨 {action}")
elif "Increase" in action:
    st.success(f"🚀 {action}")
else:
    st.info(f"✅ {action}")

# ---------------------------
# ₹ IMPACT
# ---------------------------
st.markdown("### 💰 Impact (₹)")

change_amount = portfolio_value * abs(diff) / 100

st.metric("Suggested Shift", f"₹ {int(change_amount):,}")

# ---------------------------
# MACRO SIGNALS
# ---------------------------
st.markdown("### 🧠 Macro Signals")

signals = pd.DataFrame({
    "Indicator": ["SPX", "DXY", "VIX", "US10Y"],
    "Signal": [
        latest["SPX_S"],
        latest["DXY_S"],
        latest["VIX_S"],
        latest["US10Y_S"]
    ]
})

st.table(signals)

# ---------------------------
# TREND
# ---------------------------
st.markdown("### 📈 Market Trend")

st.line_chart(df)

# ---------------------------
# FOOTER
# ---------------------------
st.caption("For informational purposes only. Not investment advice.")
