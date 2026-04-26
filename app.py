import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

@st.cache_data(ttl=3600)
def load_data():
    tickers = {
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

    try:
        raw = yf.download(list(tickers.keys()), start=start, group_by="ticker", threads=False)
    except:
        return pd.DataFrame()

    data = {}

    for t, name in tickers.items():
        try:
            sub = raw[t]
            if sub is None or sub.empty:
                continue

            col = "Adj Close" if "Adj Close" in sub.columns else "Close"
            data[name] = sub[col]
        except:
            continue

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    return df.dropna(how="all")


df = load_data()

if df.empty:
    st.warning("⚠️ Data temporarily unavailable (Yahoo limit). Refresh after 1 minute.")
    st.stop()

weekly = df.resample("W").last()

# -------------------------
# SIGNALS (SAFE)
# -------------------------
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

# -------------------------
# SCORE (ROBUST)
# -------------------------
if signal_df.empty:
    st.warning("⚠️ Limited data. Using neutral score.")
    weekly["SCORE"] = 0
else:
    weekly["SCORE"] = signal_df.sum(axis=1)

if len(weekly) == 0:
    st.warning("No data available.")
    st.stop()

latest = weekly.iloc[-1]

# -------------------------
# REGIME
# -------------------------
if latest["SCORE"] <= -2:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":20,"Bank":0,"IT":50,"Cash":30}
elif latest["SCORE"] <= 1:
    regime = "🟡 NEUTRAL"
    allocation = {"Nifty":33,"Bank":33,"IT":34,"Cash":0}
else:
    regime = "🟢 RISK ON"
    allocation = {"Nifty":50,"Bank":30,"IT":20,"Cash":0}

# -------------------------
# UI
# -------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    st.write(regime)
    st.write(f"Score: {latest['SCORE']}")

with col2:
    st.subheader("Allocation")
    st.write(allocation)

# -------------------------
# CHART (SHOW WHATEVER EXISTS)
# -------------------------
if len(weekly.columns) > 0:
    st.subheader("Market Trend")
    st.line_chart(weekly)
else:
    st.warning("No market data available for chart.")
