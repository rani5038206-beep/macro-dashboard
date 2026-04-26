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
# SAFE DOWNLOAD
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
# SIGNAL
# ===============================
def get_signal(series):
    try:
        if len(series) < 20:
            return 0
        last = float(series.iloc[-1])
        prev = float(series.iloc[-20])
        return 1 if last > prev else -1
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

# ===============================
# DECISION ENGINE
# ===============================
if score > 0.5:
    regime = "POSITIVE"
    decision = "INVEST"
    equity_alloc = 70
elif score < -0.5:
    regime = "NEGATIVE"
    decision = "REDUCE"
    equity_alloc = 30
else:
    regime = "NEUTRAL"
    decision = "HOLD"
    equity_alloc = 50

# ===============================
# HEADER
# ===============================
st.title("Macro → Micro Portfolio Engine")

c1, c2, c3 = st.columns(3)
c1.metric("Market Regime", regime)
c2.metric("Model Score", round(score,2))
c3.metric("Action", decision)

st.subheader(f"Recommended Equity Allocation: {equity_alloc}%")

# ===============================
# MACRO TABLE
# ===============================
def explain(f, s):
    mapping = {
        "SPX": ("Global support" if s==1 else "Global weakness"),
        "DXY": ("FII inflow" if s==-1 else "FII outflow"),
        "INDIAVIX": ("Stable market" if s==-1 else "Fear"),
        "USDINR": ("Strong INR" if s==-1 else "Weak INR"),
        "CRUDE": ("Low inflation" if s==-1 else "High inflation"),
        "INDIA10Y": ("Low cost" if s==-1 else "High cost")
    }
    return mapping.get(f,"")

rows = []
for k in signals:
    rows.append({
        "Factor":k,
        "Signal":signals[k],
        "Interpretation":explain(k, signals[k])
    })

st.subheader("Macro Signals")
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# STOCK ENGINE (SCREENER STYLE)
# ===============================
@st.cache_data(ttl=1800)
def get_stocks():
    universe = [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "LT.NS","ITC.NS","HINDUNILVR.NS","SBIN.NS","AXISBANK.NS",
        "BAJFINANCE.NS","KOTAKBANK.NS","ASIANPAINT.NS","MARUTI.NS",
        "TITAN.NS","SUNPHARMA.NS"
    ]

    data = []

    for s in universe:
        try:
            df = yf.download(s, period="6mo", progress=False)
            if len(df) < 60:
                continue

            close = df["Close"]

            ret = (close.iloc[-1]/close.iloc[-60]-1)*100
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

    df = pd.DataFrame(data)
    df = df[df["Return %"] > 5]
    return df.sort_values("Score", ascending=False).head(10)

stocks = get_stocks()

# ===============================
# STOCK DISPLAY
# ===============================
st.subheader("Top Stock Picks")

if stocks.empty:
    st.warning("No stocks match criteria")
else:
    st.dataframe(stocks, use_container_width=True)

# ===============================
# ALLOCATION
# ===============================
equity_amount = portfolio_value * equity_alloc / 100

if not stocks.empty:
    per_stock = equity_amount / len(stocks)
    stocks["Allocation ₹"] = round(per_stock,0)

    st.subheader("Allocation per Stock")
    st.dataframe(stocks, use_container_width=True)

# ===============================
# REBALANCE
# ===============================
st.subheader("Rebalancing Decision")

diff = equity_alloc - current_equity

if abs(diff) < 5:
    st.success("HOLD - No change")
elif diff > 0:
    st.info(f"INVEST more: Increase equity by {diff}%")
else:
    st.error(f"REDUCE equity by {abs(diff)}%")

# ===============================
# FOOTER
# ===============================
st.caption(f"Updated: {datetime.now().strftime('%d-%b %H:%M')}")
