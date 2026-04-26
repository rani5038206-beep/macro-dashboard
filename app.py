import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Macro → Micro Engine", layout="wide")

# ===============================
# USER INPUT
# ===============================
st.sidebar.header("Client Input")

portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)
current_equity = st.sidebar.slider("Current Equity %", 0, 100, 60)

st.sidebar.header("Macro Input")
india_10y = st.sidebar.number_input("India 10Y Yield (%)", value=7.1)

# ===============================
# FETCH MACRO DATA
# ===============================
@st.cache_data(ttl=3600)
def get_macro_data():
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
            data[k] = df["Close"]
        except:
            data[k] = pd.Series()

    return data

# ===============================
# SIGNAL LOGIC (FIXED ERROR)
# ===============================
def get_signal(series):
    if len(series) < 20:
        return 0
    return 1 if float(series.iloc[-1]) > float(series.iloc[-20]) else -1

# ===============================
# INDIA IMPACT LOGIC
# ===============================
def india_impact(factor, signal):
    if factor == "SPX":
        return "Positive" if signal == 1 else "Negative"
    if factor == "DXY":
        return "Negative" if signal == 1 else "Positive"
    if factor == "INDIAVIX":
        return "Negative" if signal == 1 else "Positive"
    if factor == "USDINR":
        return "Negative" if signal == 1 else "Positive"
    if factor == "CRUDE":
        return "Negative" if signal == 1 else "Positive"
    if factor == "INDIA10Y":
        return "Negative" if signal == 1 else "Positive"

# ===============================
# WHY THIS MATTERS
# ===============================
def explain(factor, signal):
    explanations = {
        "SPX": ("Global markets strong → supports India" if signal==1 else "Global weakness → risk off"),
        "DXY": ("Weak dollar → FII inflow" if signal==-1 else "Strong dollar → FII outflow"),
        "INDIAVIX": ("Low volatility → stable market" if signal==-1 else "High fear → risk"),
        "USDINR": ("Rupee strong → macro stable" if signal==-1 else "Rupee weak → pressure"),
        "CRUDE": ("Low crude → good for India" if signal==-1 else "High crude → inflation risk"),
        "INDIA10Y": ("Lower yields → growth support" if signal==-1 else "Higher yields → cost pressure")
    }
    return explanations.get(factor, "")

# ===============================
# MACRO ENGINE
# ===============================
data = get_macro_data()
signals = {k: get_signal(v) for k,v in data.items()}
signals["INDIA10Y"] = 1 if india_10y > 7 else -1

weights = {
    "SPX":0.2,
    "DXY":0.2,
    "INDIAVIX":0.15,
    "USDINR":0.15,
    "CRUDE":0.15,
    "INDIA10Y":0.15
}

score = sum(signals[k]*weights[k] for k in weights)

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
# UI HEADER
# ===============================
st.title("Macro → Micro Portfolio Engine")

col1, col2, col3 = st.columns(3)
col1.metric("Regime", regime)
col2.metric("Model Score", round(score,2))
col3.metric("Equity Allocation", f"{equity_alloc}%")

# ===============================
# MACRO TABLE
# ===============================
rows = []
for k in signals:
    rows.append({
        "Factor":k,
        "Signal":signals[k],
        "Impact":india_impact(k, signals[k]),
        "Why this matters":explain(k, signals[k])
    })

st.subheader("Macro Interpretation")
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# STOCK SELECTION ENGINE
# ===============================
@st.cache_data(ttl=3600)
def get_stocks():
    universe = [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "LT.NS","ITC.NS","HINDUNILVR.NS","SBIN.NS","AXISBANK.NS",
        "BAJFINANCE.NS","KOTAKBANK.NS","ASIANPAINT.NS","MARUTI.NS",
        "TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","WIPRO.NS"
    ]

    result = []

    for s in universe:
        try:
            df = yf.download(s, period="6mo", progress=False)
            if len(df) < 60:
                continue

            close = df["Close"]

            ret = (close.iloc[-1]/close.iloc[-60]-1)*100
            trend = 1 if close.iloc[-1] > close.iloc[-20] else -1

            score = ret + (trend*5)

            result.append({
                "Stock":s,
                "Price":round(close.iloc[-1],2),
                "Return%":round(ret,2),
                "Score":round(score,2)
            })

        except:
            continue

    df = pd.DataFrame(result)
    df = df[df["Return%"] > 5]
    df = df.sort_values("Score", ascending=False)

    return df.head(10)

top_stocks = get_stocks()

# ===============================
# ALLOCATION
# ===============================
st.subheader("Top 10 Stock Selection")

st.dataframe(top_stocks, use_container_width=True)

equity_amt = portfolio_value * equity_alloc / 100

if len(top_stocks) > 0:
    per_stock = equity_amt / len(top_stocks)

    alloc_df = top_stocks.copy()
    alloc_df["Allocation ₹"] = round(per_stock,0)

    st.subheader("Position Sizing")
    st.dataframe(alloc_df, use_container_width=True)

# ===============================
# REBALANCING ENGINE
# ===============================
st.subheader("Rebalancing Signal")

diff = equity_alloc - current_equity

if abs(diff) < 5:
    st.success("No major change needed")
elif diff > 0:
    st.info(f"Increase equity by {diff}%")
else:
    st.error(f"Reduce equity by {abs(diff)}%")

# ===============================
# LAST UPDATE
# ===============================
st.caption(f"Last updated: {datetime.now().strftime('%d-%b %H:%M')}")
