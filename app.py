import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

@st.cache_data(ttl=3600)
def load_data():
    tickers = [
        "^NSEI","^NSEBANK","^CNXIT",
        "INR=X","BZ=F","DX-Y.NYB",
        "^GSPC","^INDIAVIX","^TNX"
    ]

    try:
        df = yf.download(tickers, start=start, group_by='ticker', threads=False)
    except:
        return pd.DataFrame()

    data = {}

    mapping = {
        "^NSEI":"NIFTY",
        "^NSEBANK":"BANK",
        "^CNXIT":"IT",
        "INR=X":"USD",
        "BZ=F":"CRUDE",
        "DX-Y.NYB":"DXY",
        "^GSPC":"SPX",
        "^INDIAVIX":"VIX",
        "^TNX":"US10Y"
    }

    for ticker in tickers:
        try:
            sub = df[ticker]
            if sub is None or sub.empty:
                continue

            col = "Adj Close" if "Adj Close" in sub.columns else "Close"
            data[mapping[ticker]] = sub[col]
        except:
            continue

    if len(data) < 5:
        return pd.DataFrame()

    return pd.concat(data.values(), axis=1).dropna()


df = load_data()

if df.empty:
    st.warning("⚠️ Data temporarily unavailable. Please refresh after 1 minute.")
    st.stop()

weekly = df.resample("W").last()

required = ["DXY","SPX","VIX","US10Y","NIFTY","BANK","IT"]
missing = [c for c in required if c not in weekly.columns]

if missing:
    st.error(f"Missing data: {missing}")
    st.stop()

weekly["DXY_S"] = np.where(weekly["DXY"] > weekly["DXY"].rolling(20).mean(), -1, 1)
weekly["SPX_S"] = np.where(weekly["SPX"] > weekly["SPX"].rolling(20).mean(), 1, -1)
weekly["VIX_S"] = np.where(weekly["VIX"] > weekly["VIX"].rolling(10).mean(), -1, 1)
weekly["USY_S"] = np.where(weekly["US10Y"] > weekly["US10Y"].rolling(20).mean(), -1, 1)

weekly["SCORE"] = weekly[["DXY_S","SPX_S","VIX_S","USY_S"]].sum(axis=1)

latest = weekly.iloc[-1]

if latest["SCORE"] <= -2:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":20,"Bank":0,"IT":50,"Cash":30}
elif latest["SCORE"] <= 1:
    regime = "🟡 NEUTRAL"
    allocation = {"Nifty":33,"Bank":33,"IT":34,"Cash":0}
else:
    regime = "🟢 RISK ON"
    allocation = {"Nifty":50,"Bank":30,"IT":20,"Cash":0}

col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    st.write(regime)
    st.write(f"Score: {latest['SCORE']}")

with col2:
    st.subheader("Allocation")
    st.write(allocation)

st.subheader("Market Trend")
st.line_chart(weekly[["NIFTY","BANK","IT"]])
