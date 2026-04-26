import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Macro → Micro Engine", layout="wide")

# ===============================
# 📊 FETCH MACRO DATA
# ===============================
@st.cache_data(ttl=3600)
def get_macro_data():
    data = {}

    def safe_download(ticker):
        try:
            df = yf.download(ticker, period="3mo", progress=False)
            return df["Close"].dropna()
        except:
            return pd.Series()

    data["SPX"] = safe_download("^GSPC")
    data["DXY"] = safe_download("DX-Y.NYB")
    data["INDIAVIX"] = safe_download("^INDIAVIX")
    data["USDINR"] = safe_download("INR=X")
    data["CRUDE"] = safe_download("CL=F")
    data["INDIA10Y"] = safe_download("^TNX")  # proxy

    return data

# ===============================
# 📈 SIGNAL LOGIC
# ===============================
def get_signal(series):
    if len(series) < 20:
        return 0
    return 1 if series.iloc[-1] > series.iloc[-20] else -1

# ===============================
# 🇮🇳 INDIA IMPACT LOGIC
# ===============================
def india_impact(factor, signal):
    if factor == "SPX":
        return "Positive" if signal == 1 else "Negative"

    elif factor == "DXY":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "INDIAVIX":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "INDIA10Y":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "USDINR":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "CRUDE":
        return "Negative" if signal == 1 else "Positive"

    return "Neutral"

# ===============================
# 🧠 WHY THIS MATTERS (CLIENT TEXT)
# ===============================
def why_text(factor, signal):
    if factor == "SPX":
        return "Global markets are strong → risk appetite improves → supports Indian equities" if signal == 1 else "Global weakness → risk-off → pressure on Indian markets"

    if factor == "DXY":
        return "Dollar strengthening → FIIs may pull money out of India" if signal == 1 else "Weak dollar → FII inflows likely → positive for equities"

    if factor == "INDIAVIX":
        return "Low volatility → stable market → supports equity investments" if signal == -1 else "High volatility → fear → risk reduction"

    if factor == "USDINR":
        return "Rupee weakening → imported inflation → negative for equities" if signal == 1 else "Rupee stable/strong → confidence in economy"

    if factor == "CRUDE":
        return "Rising crude → inflation + fiscal pressure → negative for India" if signal == 1 else "Falling crude → margin + consumption boost"

    if factor == "INDIA10Y":
        return "Bond yields rising → cost of capital up → equities less attractive" if signal == 1 else "Lower yields → equity valuations supported"

    return ""

# ===============================
# 🏭 SECTOR IMPACT ENGINE
# ===============================
def sector_impact(signals):
    sector = {
        "IT": 0,
        "BANKS": 0,
        "FMCG": 0,
        "AUTO": 0,
        "INFRA": 0,
        "PHARMA": 0
    }

    # DXY impact (IT)
    sector["IT"] += -signals["DXY"]

    # Interest rate impact
    sector["BANKS"] += -signals["INDIA10Y"]
    sector["AUTO"] += -signals["INDIA10Y"]

    # Crude impact
    sector["AUTO"] += -signals["CRUDE"]
    sector["FMCG"] += -signals["CRUDE"]

    # Volatility
    for s in sector:
        sector[s] += -signals["INDIAVIX"]

    # Global growth
    for s in sector:
        sector[s] += signals["SPX"]

    return sector

# ===============================
# 📊 MACRO CALCULATION
# ===============================
data = get_macro_data()

signals = {k: get_signal(v) for k, v in data.items()}

weights = {
    "SPX": 0.2,
    "DXY": 0.2,
    "INDIAVIX": 0.15,
    "USDINR": 0.15,
    "CRUDE": 0.15,
    "INDIA10Y": 0.15
}

score = sum(signals[k] * weights[k] for k in signals)

# ===============================
# 📊 REGIME
# ===============================
if score > 0.5:
    regime = "RISK ON"
    equity_alloc = 70
elif score < -0.5:
    regime = "RISK OFF"
    equity_alloc = 30
else:
    regime = "TRANSITION"
    equity_alloc = 50

# ===============================
# 🎯 UI
# ===============================
st.title("📊 Macro → Micro Portfolio Engine")

col1, col2, col3 = st.columns(3)
col1.metric("Regime", regime)
col2.metric("Model Score", round(score, 2))
col3.metric("Recommended Equity %", f"{equity_alloc}%")

# ===============================
# 📊 MACRO TABLE
# ===============================
st.subheader("Macro Interpretation")

rows = []
for k in signals:
    rows.append({
        "Factor": k,
        "Signal": signals[k],
        "Impact (India)": india_impact(k, signals[k]),
        "Why this matters": why_text(k, signals[k])
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# 🏭 SECTOR VIEW
# ===============================
st.subheader("Sector Impact")

sector_scores = sector_impact(signals)
sector_df = pd.DataFrame({
    "Sector": list(sector_scores.keys()),
    "Score": list(sector_scores.values())
}).sort_values("Score", ascending=False)

st.dataframe(sector_df, use_container_width=True)

# ===============================
# 📊 CLIENT INPUT
# ===============================
st.sidebar.header("Client Input")

portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)
current_equity = st.sidebar.slider("Current Equity %", 0, 100, 60)

# ===============================
# ⚠️ ACTION
# ===============================
st.subheader("Action Required")

if current_equity > equity_alloc:
    st.error(f"Reduce equity by {current_equity - equity_alloc}%")
elif current_equity < equity_alloc:
    st.success(f"Increase equity by {equity_alloc - current_equity}%")
else:
    st.info("Portfolio aligned")

# ===============================
# 💰 PORTFOLIO IMPACT
# ===============================
st.subheader("Portfolio Impact")

current_equity_amt = portfolio_value * current_equity / 100
recommended_equity_amt = portfolio_value * equity_alloc / 100

col1, col2 = st.columns(2)
col1.metric("Current Equity", f"₹{int(current_equity_amt):,}")
col2.metric("Recommended Equity", f"₹{int(recommended_equity_amt):,}")

# ===============================
# 📈 STOCK PICKS (SIMPLE)
# ===============================
st.subheader("Top Stock Picks")

stocks = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "TCS.NS"]

allocation_per_stock = recommended_equity_amt / len(stocks)

for s in stocks:
    st.write(f"{s} → ₹{int(allocation_per_stock):,}")
