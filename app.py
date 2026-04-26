import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time

st.set_page_config(page_title="Macro → Micro Engine", layout="wide")

# ===============================
# SAFE DATA FETCH
# ===============================
@st.cache_data(ttl=3600)
def fetch_data():
    tickers = {
        "SPX": "^GSPC",
        "DXY": "DX-Y.NYB",
        "INDIAVIX": "^INDIAVIX",
        "USDINR": "INR=X",
        "CRUDE": "CL=F"
    }

    data = {}

    for k, t in tickers.items():
        try:
            df = yf.download(t, period="3mo", progress=False)
            time.sleep(1)

            if df.empty:
                data[k] = pd.Series()
            else:
                close = df["Close"]

                # Ensure 1D
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                data[k] = close.dropna()

        except:
            data[k] = pd.Series()

    return data

# ===============================
# SIGNAL FUNCTION (FIXED)
# ===============================
def get_signal(series):
    try:
        if series is None or len(series) < 20:
            return 0

        series = series.dropna()

        if len(series) < 20:
            return 0

        last = float(series.iloc[-1])
        prev = float(series.iloc[-20])

        return 1 if last > prev else -1

    except:
        return 0

# ===============================
# INDIA IMPACT LOGIC
# ===============================
def india_impact(factor, signal):
    if factor == "SPX":
        return "Positive" if signal == 1 else "Negative"

    elif factor == "DXY":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "INDIAVIX":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "USDINR":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "CRUDE":
        return "Negative" if signal == 1 else "Positive"

    elif factor == "INDIA10Y":
        return "Negative" if signal == 1 else "Positive"

    return "Neutral"

# ===============================
# WHY TEXT (CLIENT LANGUAGE)
# ===============================
def why_text(factor, signal):
    if factor == "SPX":
        return "Global markets strong → supports Indian equities" if signal == 1 else "Global weakness → risk-off sentiment"

    if factor == "DXY":
        return "Strong dollar → FII outflow risk" if signal == 1 else "Weak dollar → FII inflows likely"

    if factor == "INDIAVIX":
        return "Low volatility → stable markets" if signal == -1 else "High volatility → fear in market"

    if factor == "USDINR":
        return "Weak rupee → inflation risk" if signal == 1 else "Strong rupee → macro stability"

    if factor == "CRUDE":
        return "High crude → inflation + margin pressure" if signal == 1 else "Low crude → positive for economy"

    if factor == "INDIA10Y":
        return "High yields → cost of capital up" if signal == 1 else "Lower yields → equity supportive"

    return ""

# ===============================
# SECTOR IMPACT ENGINE
# ===============================
def sector_impact(signals):
    sector = {
        "IT": 0,
        "BANKS": 0,
        "FMCG": 0,
        "AUTO": 0,
        "INFRA": 0
    }

    # DXY → IT
    sector["IT"] += -signals["DXY"]

    # Rates
    sector["BANKS"] += -signals["INDIA10Y"]
    sector["AUTO"] += -signals["INDIA10Y"]

    # Crude
    sector["AUTO"] += -signals["CRUDE"]
    sector["FMCG"] += -signals["CRUDE"]

    # Volatility
    for s in sector:
        sector[s] += -signals["INDIAVIX"]

    # Global trend
    for s in sector:
        sector[s] += signals["SPX"]

    return sector

# ===============================
# LOAD DATA
# ===============================
data = fetch_data()

signals = {k: get_signal(v) for k, v in data.items()}

# INDIA 10Y → MANUAL INPUT (IMPORTANT)
india_10y = st.sidebar.number_input("India 10Y Yield (%)", value=7.1)

signals["INDIA10Y"] = 1 if india_10y > 7 else -1

# ===============================
# MODEL SCORE
# ===============================
weights = {
    "SPX": 0.2,
    "DXY": 0.2,
    "INDIAVIX": 0.15,
    "USDINR": 0.15,
    "CRUDE": 0.15,
    "INDIA10Y": 0.15
}

score = sum(signals[k] * weights[k] for k in weights)

# ===============================
# REGIME
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
# UI
# ===============================
st.title("📊 Macro → Micro Portfolio Engine")

c1, c2, c3 = st.columns(3)
c1.metric("Regime", regime)
c2.metric("Score", round(score, 2))
c3.metric("Equity Allocation", f"{equity_alloc}%")

# ===============================
# MACRO TABLE
# ===============================
st.subheader("Macro Interpretation")

rows = []
for k in signals:
    rows.append({
        "Factor": k,
        "Signal": signals[k],
        "Impact": india_impact(k, signals[k]),
        "Why this matters": why_text(k, signals[k])
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# SECTOR VIEW
# ===============================
st.subheader("Sector Impact")

sector_scores = sector_impact(signals)

sector_df = pd.DataFrame({
    "Sector": list(sector_scores.keys()),
    "Score": list(sector_scores.values())
}).sort_values("Score", ascending=False)

st.dataframe(sector_df, use_container_width=True)

# ===============================
# CLIENT INPUT
# ===============================
st.sidebar.header("Client Input")

portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)
current_equity = st.sidebar.slider("Current Equity %", 0, 100, 60)

# ===============================
# ACTION
# ===============================
st.subheader("Action Required")

if current_equity > equity_alloc:
    st.error(f"Reduce equity by {current_equity - equity_alloc}%")
elif current_equity < equity_alloc:
    st.success(f"Increase equity by {equity_alloc - current_equity}%")
else:
    st.info("Portfolio aligned")

# ===============================
# PORTFOLIO IMPACT
# ===============================
st.subheader("Portfolio Impact")

curr_eq_amt = portfolio_value * current_equity / 100
rec_eq_amt = portfolio_value * equity_alloc / 100

col1, col2 = st.columns(2)
col1.metric("Current Equity ₹", f"{int(curr_eq_amt):,}")
col2.metric("Recommended Equity ₹", f"{int(rec_eq_amt):,}")

# ===============================
# STOCK ALLOCATION
# ===============================
st.subheader("Top Stock Allocation")

stocks = ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS"]

per_stock = rec_eq_amt / len(stocks)

for s in stocks:
    st.write(f"{s} → ₹{int(per_stock):,}")
