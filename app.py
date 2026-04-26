import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Macro → Micro Engine", layout="wide")

# ===============================
# INPUT
# ===============================
st.sidebar.header("Client Input")

portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)
current_equity = st.sidebar.slider("Current Equity %", 0, 100, 60)

st.sidebar.header("Macro Input")
india_10y = st.sidebar.number_input("India 10Y Yield (%)", value=7.1)

# ===============================
# SAFE DATA
# ===============================
def safe_download(ticker):
    try:
        df = yf.download(ticker, period="3mo", progress=False)
        if df.empty:
            return pd.Series(dtype=float)
        return df["Close"].dropna()
    except:
        return pd.Series(dtype=float)

# ===============================
# SIGNAL (INDIA IMPACT LOGIC)
# ===============================
def get_signal(series):
    try:
        if len(series) < 20:
            return 0
        return 1 if float(series.iloc[-1]) > float(series.iloc[-20]) else -1
    except:
        return 0

# ===============================
# MACRO DATA
# ===============================
data = {
    "SPX": safe_download("^GSPC"),
    "DXY": safe_download("DX-Y.NYB"),
    "INDIAVIX": safe_download("^INDIAVIX"),
    "USDINR": safe_download("INR=X"),
    "CRUDE": safe_download("CL=F"),
}

signals = {k: get_signal(v) for k, v in data.items()}

# INDIA IMPACT FIX
signals["DXY"] *= -1          # strong dollar = bad
signals["INDIAVIX"] *= -1     # high vix = bad
signals["USDINR"] *= -1       # rising USDINR = bad
signals["CRUDE"] *= -1        # rising crude = bad

# India Bond Yield
signals["INDIA10Y"] = -1 if india_10y > 7 else 1

# ===============================
# SCORE CALCULATION
# ===============================
weights = {
    "SPX":0.2,
    "DXY":0.2,
    "INDIAVIX":0.15,
    "USDINR":0.15,
    "CRUDE":0.15,
    "INDIA10Y":0.15
}

score_raw = sum(signals[k]*weights[k] for k in weights)

# Convert to %
score_percent = round((score_raw + 1) * 50, 1)

# ===============================
# DECISION
# ===============================
if score_percent >= 70:
    decision = "🟢 BUY INDIA"
    equity_alloc = 70
elif score_percent >= 51:
    decision = "🟡 HOLD"
    equity_alloc = 50
else:
    decision = "🔴 REDUCE / FEAR"
    equity_alloc = 30

# ===============================
# HEADER
# ===============================
st.title("Macro → Micro Portfolio Engine")

c1, c2, c3 = st.columns(3)
c1.metric("India Score %", f"{score_percent}%")
c2.metric("Decision", decision)
c3.metric("Equity Allocation", f"{equity_alloc}%")

# ===============================
# MACRO TABLE
# ===============================
def explain(k, s):
    mapping = {
        "SPX": "Global support" if s==1 else "Global weakness",
        "DXY": "Weak dollar → FII inflow" if s==1 else "Strong dollar → FII outflow",
        "INDIAVIX": "Low volatility → Stable" if s==1 else "High volatility → Fear",
        "USDINR": "Strong INR → Positive" if s==1 else "Weak INR → Negative",
        "CRUDE": "Low crude → Low inflation" if s==1 else "High crude → Inflation risk",
        "INDIA10Y": "Low yield → Cheap capital" if s==1 else "High yield → Expensive capital"
    }
    return mapping.get(k, "")

rows = []
for k in signals:
    rows.append({
        "Factor":k,
        "Signal":signals[k],
        "Impact":"Positive" if signals[k]==1 else "Negative",
        "Why it matters":explain(k, signals[k])
    })

st.subheader("Macro Interpretation")
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# STOCK SELECTION (FIXED)
# ===============================
@st.cache_data(ttl=1800)
def get_stocks():
    universe = [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "LT.NS","ITC.NS","HINDUNILVR.NS","SBIN.NS","AXISBANK.NS",
        "BAJFINANCE.NS","KOTAKBANK.NS"
    ]

    data = []

    for s in universe:
        try:
            df = yf.download(s, period="6mo", progress=False)
            if len(df) < 60:
                continue

            close = df["Close"]

            ret = float((close.iloc[-1]/close.iloc[-60]-1)*100)
            trend = 1 if close.iloc[-1] > close.iloc[-20] else -1

            score = ret + trend*5

            data.append({
                "Stock":s,
                "Return %":round(ret,2),
                "Trend":trend,
                "Score":round(score,2)
            })

        except:
            continue

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # FIX: avoid KeyError
    if "Return %" not in df.columns:
        return pd.DataFrame()

    df = df[df["Return %"] > 5]

    return df.sort_values("Score", ascending=False).head(10)

stocks = get_stocks()

# ===============================
# DISPLAY STOCKS
# ===============================
st.subheader("Top Stock Picks")

if stocks.empty:
    st.warning("No stocks passed screener")
else:
    st.dataframe(stocks, use_container_width=True)

# ===============================
# ALLOCATION
# ===============================
equity_amount = portfolio_value * equity_alloc / 100

if not stocks.empty:
    per_stock = equity_amount / len(stocks)
    stocks["Allocation ₹"] = round(per_stock,0)

    st.subheader("Position Sizing (₹ per stock)")
    st.dataframe(stocks, use_container_width=True)

# ===============================
# REBALANCE
# ===============================
st.subheader("Rebalancing")

diff = equity_alloc - current_equity

if abs(diff) < 5:
    st.success("HOLD – No major change")
elif diff > 0:
    st.info(f"Increase Equity by {diff}%")
else:
    st.error(f"Reduce Equity by {abs(diff)}%")

# ===============================
# FOOTER
# ===============================
st.caption(f"Last Updated: {datetime.now().strftime('%d-%b %H:%M')}")
