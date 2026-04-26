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
# SAFE MACRO DATA FETCH
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

            if df.empty or "Close" not in df:
                data[k] = pd.Series(dtype=float)
            else:
                data[k] = df["Close"].dropna()

        except:
            data[k] = pd.Series(dtype=float)

    return data

# ===============================
# ROBUST SIGNAL FUNCTION
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
    mapping = {
        "SPX": (1, -1),
        "DXY": (-1, 1),
        "INDIAVIX": (-1, 1),
        "USDINR": (-1, 1),
        "CRUDE": (-1, 1),
        "INDIA10Y": (-1, 1)
    }

    pos, neg = mapping.get(factor, (0, 0))
    return "Positive" if signal == pos else "Negative"

# ===============================
# EXPLANATION ENGINE
# ===============================
def explain(factor, signal):
    logic = {
        "SPX": ("Global markets strong → supports India" if signal==1 else "Global weakness → risk off"),
        "DXY": ("Weak dollar → FII inflow" if signal==-1 else "Strong dollar → FII outflow"),
        "INDIAVIX": ("Low volatility → stable market" if signal==-1 else "High volatility → fear"),
        "USDINR": ("Rupee strong → stability" if signal==-1 else "Rupee weak → pressure"),
        "CRUDE": ("Low crude → good for India" if signal==-1 else "High crude → inflation risk"),
        "INDIA10Y": ("Lower yields → growth support" if signal==-1 else "Higher yields → cost pressure")
    }
    return logic.get(factor, "")

# ===============================
# MACRO ENGINE
# ===============================
data = get_macro_data()

signals = {}
for k, v in data.items():
    signals[k] = get_signal(v)

# manual India 10Y
signals["INDIA10Y"] = 1 if india_10y > 7 else -1

weights = {
    "SPX":0.2,
    "DXY":0.2,
    "INDIAVIX":0.15,
    "USDINR":0.15,
    "CRUDE":0.15,
    "INDIA10Y":0.15
}

score = sum(signals.get(k,0)*weights[k] for k in weights)

# REGIME
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
# HEADER
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
for k in weights:
    rows.append({
        "Factor":k,
        "Signal":signals.get(k,0),
        "Impact":india_impact(k, signals.get(k,0)),
        "Why this matters":explain(k, signals.get(k,0))
    })

st.subheader("Macro Interpretation")
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# STOCK ENGINE
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

            if df.empty or len(df) < 60:
                continue

            close = df["Close"].dropna()

            if len(close) < 60:
                continue

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

    if df.empty:
        return df

    df = df[df["Return%"] > 5]
    df = df.sort_values("Score", ascending=False)

    return df.head(10)

top_stocks = get_stocks()

# ===============================
# DISPLAY STOCKS
# ===============================
st.subheader("Top 10 Stock Selection")

if top_stocks.empty:
    st.warning("No stocks passed filter today")
else:
    st.dataframe(top_stocks, use_container_width=True)

# ===============================
# POSITION SIZING
# ===============================
equity_amt = portfolio_value * equity_alloc / 100

if not top_stocks.empty:
    per_stock = equity_amt / len(top_stocks)

    alloc_df = top_stocks.copy()
    alloc_df["Allocation ₹"] = round(per_stock,0)

    st.subheader("Position Sizing (₹ per stock)")
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
# FOOTER
# ===============================
st.caption(f"Last updated: {datetime.now().strftime('%d-%b %H:%M')}")
