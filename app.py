import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from pandas_datareader import data as pdr

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

@st.cache_data(ttl=3600)
def load_data():
    data = {}

    # ------------------------
    # INDIA MARKET (Yahoo OK)
    # ------------------------
    tickers = {
        "^NSEI": "NIFTY",
        "^NSEBANK": "BANK",
        "^CNXIT": "IT"
    }

    for t, name in tickers.items():
        try:
            df = yf.download(t, start=start, progress=False)
            col = "Adj Close" if "Adj Close" in df.columns else "Close"
            data[name] = df[col]
        except:
            pass

    # ------------------------
    # US MARKETS (Yahoo)
    # ------------------------
    try:
        spx = yf.download("^GSPC", start=start, progress=False)
        data["SPX"] = spx["Close"]
    except:
        pass

    try:
        vix = yf.download("^VIX", start=start, progress=False)
        data["VIX"] = vix["Close"]
    except:
        pass

    try:
        dxy = yf.download("DX-Y.NYB", start=start, progress=False)
        data["DXY"] = dxy["Close"]
    except:
        pass

    # ------------------------
    # US 10Y (FRED - STRONG)
    # ------------------------
    try:
        us10y = pdr.DataReader("DGS10", "fred", start)
        data["US10Y"] = us10y["DGS10"]
    except:
        pass

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    return df.dropna(how="all")


df = load_data()

if df.empty:
    st.warning("⚠️ Data not available. Try again.")
    st.stop()

weekly = df.resample("W").last()

# ------------------------
# SIGNALS (SMART)
# ------------------------
signals = {}

if "DXY" in weekly:
    signals["DXY"] = np.where(weekly["DXY"] > weekly["DXY"].rolling(20).mean(), -1, 1)

if "SPX" in weekly:
    signals["SPX"] = np.where(weekly["SPX"] > weekly["SPX"].rolling(20).mean(), 1, -1)

if "VIX" in weekly:
    signals["VIX"] = np.where(weekly["VIX"] > weekly["VIX"].rolling(10).mean(), -1, 1)

if "US10Y" in weekly:
    signals["US10Y"] = np.where(weekly["US10Y"] > weekly["US10Y"].rolling(20).mean(), -1, 1)

signal_df = pd.DataFrame(signals)

if signal_df.empty:
    weekly["SCORE"] = 0
else:
    weekly["SCORE"] = signal_df.sum(axis=1)

latest = weekly.iloc[-1]

# ------------------------
# REGIME
# ------------------------
if latest["SCORE"] <= -2:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":20,"Bank":0,"IT":50,"Cash":30}
elif latest["SCORE"] <= 1:
    regime = "🟡 NEUTRAL"
    allocation = {"Nifty":33,"Bank":33,"IT":34,"Cash":0}
else:
    regime = "🟢 RISK ON"
    allocation = {"Nifty":50,"Bank":30,"IT":20,"Cash":0}

# ------------------------
# UI
# ------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    st.write(regime)
    st.write(f"Score: {latest['SCORE']}")

with col2:
    st.subheader("Allocation")
    st.write(allocation)

st.subheader("Market Trend")
st.line_chart(weekly)
