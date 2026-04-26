import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Client Dashboard", layout="wide")

# ---------------------------
# LOAD DATA
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
    st.error("❌ Data not loading")
    st.stop()

# ---------------------------
# SIGNALS
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
# REGIME
# ---------------------------
if score >= 2:
    regime = "RISK ON"
    color = "🟢"
    allocation = {"Equity": 80, "Cash": 20}
    message = "Increase equity exposure"
    reason = "Strong trend + low volatility + weak dollar"
elif score <= -2:
    regime = "RISK OFF"
    color = "🔴"
    allocation = {"Equity": 40, "Cash": 60}
    message = "Reduce equity exposure"
    reason = "High volatility + strong dollar + weak trend"
else:
    regime = "TRANSITION"
    color = "🟡"
    allocation = {"Equity": 60, "Cash": 40}
    message = "Maintain balanced allocation"
    reason = "Mixed macro signals"

# ---------------------------
# SIDEBAR (UPGRADED)
# ---------------------------
st.sidebar.header("👤 Client Profile")

client_name = st.sidebar.text_input("Client Name", "Client A")

equity = st.sidebar.slider("Equity %", 0, 100, 60)
cash = 100 - equity

portfolio_value = st.sidebar.number_input(
    "Portfolio Value (₹)", value=1000000
)

# ---------------------------
# HEADER
# ---------------------------
st.title(f"📊 {client_name} - Portfolio Dashboard")

st.markdown("### 📌 Market Snapshot")

col1, col2, col3 = st.columns(3)

col1.metric("Market Regime", f"{color} {regime}")
col2.metric("Model Score", f"{score:.1f}")
col3.metric("Last Updated", df.index[-1].strftime("%d %b %Y"))

# ---------------------------
# ADVISORY
# ---------------------------
st.markdown("### 📢 Advisory Decision")

if "Reduce" in message:
    st.error(f"🚨 {message}")
elif "Increase" in message:
    st.success(f"🚀 {message}")
else:
    st.warning(f"⚖️ {message}")

st.markdown(f"**Why? → {reason}**")

# ---------------------------
# COMPARISON
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
# ACTION ENGINE (STRONG)
# ---------------------------
st.markdown("### 🚨 Final Recommendation")

diff = model_alloc["Equity"] - equity
change_amount = portfolio_value * abs(diff) / 100

if diff > 10:
    st.success(f"🚀 BUY EQUITY: Increase by {diff}% (₹ {int(change_amount):,})")
elif diff < -10:
    st.error(f"🚨 SELL EQUITY: Reduce by {abs(diff)}% (₹ {int(change_amount):,})")
else:
    st.info("✅ HOLD: No major change required")

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
