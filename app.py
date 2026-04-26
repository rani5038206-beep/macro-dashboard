import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time

st.set_page_config(page_title="Macro → Micro Engine", layout="wide")

# ===============================
# DATA FETCH (SAFE)
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
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]

                data[k] = close.dropna()

        except:
            data[k] = pd.Series()

    return data


# ===============================
# SIGNAL (TREND)
# ===============================
def get_signal(series):
    try:
        if len(series) < 20:
            return 0

        series = series.dropna()
        last = float(series.iloc[-1])
        prev = float(series.iloc[-20])

        return 1 if last > prev else -1
    except:
        return 0


# ===============================
# LEVEL CHECK (NEW)
# ===============================
def level_signal(factor, value):
    if factor == "CRUDE":
        if value > 85:
            return -1
        elif value < 70:
            return 1

    if factor == "INDIAVIX":
        if value > 20:
            return -1
        elif value < 13:
            return 1

    if factor == "INDIA10Y":
        if value > 7.5:
            return -1
        elif value < 6.8:
            return 1

    if factor == "USDINR":
        if value > 84:
            return -1
        elif value < 82:
            return 1

    return 0


# ===============================
# WHY TEXT (CORRECTED)
# ===============================
def why_text(factor, trend, level):
    if factor == "CRUDE":
        return "Crude falling → inflation easing → positive" if trend == -1 else "Crude rising → inflation pressure"

    if factor == "USDINR":
        return "Rupee strengthening → stability" if trend == -1 else "Rupee weakening → inflation risk"

    if factor == "DXY":
        return "Weak dollar → FII inflow" if trend == -1 else "Strong dollar → FII outflow"

    if factor == "INDIAVIX":
        return "Low volatility → stable markets" if trend == -1 else "High volatility → fear"

    if factor == "INDIA10Y":
        return "Lower yields → equity support" if trend == -1 else "Higher yields → cost pressure"

    if factor == "SPX":
        return "Global markets strong → supports India" if trend == 1 else "Global weakness → risk-off"

    return ""


# ===============================
# IMPACT (FINAL)
# ===============================
def final_signal(trend, level):
    return trend + level


# ===============================
# LOAD DATA
# ===============================
data = fetch_data()

trend_signals = {k: get_signal(v) for k, v in data.items()}

# India 10Y manual
india_10y = st.sidebar.number_input("India 10Y Yield (%)", value=7.1)
trend_signals["INDIA10Y"] = 1 if india_10y > 7 else -1

# ===============================
# LEVEL SIGNALS
# ===============================
latest_values = {
    k: float(v.iloc[-1]) if len(v) > 0 else 0
    for k, v in data.items()
}
latest_values["INDIA10Y"] = india_10y

level_signals = {
    k: level_signal(k, latest_values[k])
    for k in latest_values
}

# ===============================
# FINAL SIGNAL
# ===============================
signals = {
    k: final_signal(trend_signals[k], level_signals[k])
    for k in trend_signals
}

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
        "Trend": trend_signals[k],
        "Level": level_signals[k],
        "Final Signal": signals[k],
        "Why this matters": why_text(k, trend_signals[k], level_signals[k])
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# SECTOR IMPACT
# ===============================
def sector_impact(signals):
    sector = {
        "IT": -signals["DXY"],
        "BANKS": -signals["INDIA10Y"],
        "FMCG": -signals["CRUDE"],
        "AUTO": -signals["CRUDE"],
        "INFRA": signals["SPX"]
    }
    return sector

st.subheader("Sector Impact")

sector_df = pd.DataFrame({
    "Sector": sector_impact(signals).keys(),
    "Score": sector_impact(signals).values()
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
