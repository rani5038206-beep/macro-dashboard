import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Caring Click Dashboard", layout="wide")

# ---------------------------
# DATA LOADING (SAFE)
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
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if not df.empty:
                data[name] = df["Close"]
        except:
            pass

    if len(data) == 0:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    df = df.dropna()

    return df


df = load_data()

if df is None or df.empty:
    st.error("❌ Data not loading. Try again later.")
    st.stop()

# ---------------------------
# SIGNALS
# ---------------------------
weekly = df.resample("W").last()

for col in weekly.columns:
    weekly[f"{col}_S"] = np.where(
        weekly[col] > weekly[col].rolling(20).mean(),
        1,
        -1
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
    allocation = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
    message = "Increase equity exposure."
elif score <= -2:
    regime = "RISK OFF"
    color = "🔴"
    allocation = {"Nifty": 20, "Bank": 20, "IT": 10, "Cash": 50}
    message = "Reduce equity exposure."
else:
    regime = "TRANSITION"
    color = "🟡"
    allocation = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}
    message = "Balanced approach advised."

# ---------------------------
# HEADER
# ---------------------------
st.title("📊 Caring Click - Client Dashboard")

st.subheader("📌 Market Snapshot")

col1, col2, col3 = st.columns(3)

col1.metric("Regime", f"{color} {regime}")
col2.metric("Model Score", f"{score:.1f}")
col3.metric("Last Updated", df.index[-1].strftime("%d %b %Y"))

# ---------------------------
# ADVISORY
# ---------------------------
st.markdown("### 📢 Advisory Note")
st.warning(message)

# ---------------------------
# CLIENT INPUT
# ---------------------------
st.sidebar.header("👤 Client Portfolio")

equity = st.sidebar.slider("Equity %", 0, 100, 60)
cash = st.sidebar.slider("Cash %", 0, 100, 40)

portfolio_value = st.sidebar.number_input(
    "Portfolio Value (₹)", value=1000000
)

# ---------------------------
# COMPARISON
# ---------------------------
st.subheader("⚖️ Portfolio Comparison")

client_alloc = {"Equity": equity, "Cash": cash}
model_equity = 100 - allocation["Cash"]
model_alloc = {"Equity": model_equity, "Cash": allocation["Cash"]}

comparison = pd.DataFrame({
    "Client": client_alloc,
    "Model": model_alloc
})

st.bar_chart(comparison.T)

# ---------------------------
# ACTION ENGINE
# ---------------------------
st.subheader("🚨 Action Required")

diff = model_equity - equity

if diff > 10:
    action = f"Increase Equity by {diff}%"
elif diff < -10:
    action = f"Reduce Equity by {abs(diff)}%"
else:
    action = "Hold Current Allocation"

if "Reduce" in action:
    st.error(f"🚨 {action}")
elif "Increase" in action:
    st.success(f"🚀 {action}")
else:
    st.info(f"✅ {action}")

# ---------------------------
# ₹ IMPACT
# ---------------------------
st.subheader("💰 Suggested Change (₹)")

change_amount = portfolio_value * abs(diff) / 100

st.write(f"Suggested Shift: ₹ {int(change_amount):,}")

# ---------------------------
# MACRO SIGNALS
# ---------------------------
st.subheader("🧠 Macro Signals (Latest)")

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
# MARKET TREND
# ---------------------------
st.subheader("📈 Market Trend")

st.line_chart(df)

# ---------------------------
# FOOTER
# ---------------------------
st.caption("For informational purposes only. Not investment advice.")
