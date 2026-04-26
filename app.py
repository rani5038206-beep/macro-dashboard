import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

# =========================
# DATA LOADER (ROBUST)
# =========================
@st.cache_data(ttl=3600)
def load_data():
    tickers = {
        "^NSEI": "NIFTY",
        "^NSEBANK": "BANK",
        "^CNXIT": "IT",
        "^GSPC": "SPX",
        "^VIX": "VIX",
        "^TNX": "US10Y",
        "DX-Y.NYB": "DXY"
    }

    data = {}

    for t, name in tickers.items():
        try:
            df = yf.download(t, start=start, progress=False, threads=False)

            if df is None or df.empty:
                continue

            col = "Adj Close" if "Adj Close" in df.columns else "Close"
            data[name] = df[col]

            time.sleep(1)  # avoid rate limit

        except:
            continue

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.concat(data.values(), axis=1)
    df.columns = list(data.keys())

    return df.dropna(how="all")


df = load_data()

if df.empty:
    st.warning("⚠️ Data unavailable. Refresh after 1 minute.")
    st.stop()

weekly = df.resample("W").last()

# =========================
# SIGNALS (SAFE + NO NaN)
# =========================
signals = {}

if "DXY" in weekly:
    dxy_ma = weekly["DXY"].rolling(20).mean()
    signals["DXY"] = np.where(weekly["DXY"] > dxy_ma, -1, 1)

if "SPX" in weekly:
    spx_ma = weekly["SPX"].rolling(20).mean()
    signals["SPX"] = np.where(weekly["SPX"] > spx_ma, 1, -1)

if "VIX" in weekly:
    vix_ma = weekly["VIX"].rolling(10).mean()
    signals["VIX"] = np.where(weekly["VIX"] > vix_ma, -1, 1)

if "US10Y" in weekly:
    usy_ma = weekly["US10Y"].rolling(20).mean()
    signals["US10Y"] = np.where(weekly["US10Y"] > usy_ma, -1, 1)

signal_df = pd.DataFrame(signals)

# =========================
# SCORE (FIXED PROPERLY)
# =========================
if signal_df.empty:
    st.warning("⚠️ Limited data. Using neutral score.")
    weekly["SCORE"] = 0
else:
    signal_df = signal_df.fillna(0)  # 🔥 critical fix
    weekly["SCORE"] = signal_df.sum(axis=1)

latest = weekly.iloc[-1]

# safety fix
if pd.isna(latest["SCORE"]):
    latest["SCORE"] = 0

# =========================
# REGIME LOGIC
# =========================
if latest["SCORE"] <= -2:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":20,"Bank":0,"IT":50,"Cash":30}
elif latest["SCORE"] <= 1:
    regime = "🟡 NEUTRAL"
    allocation = {"Nifty":33,"Bank":33,"IT":34,"Cash":0}
else:
    regime = "🟢 RISK ON"
    allocation = {"Nifty":50,"Bank":30,"IT":20,"Cash":0}

# =========================
# UI DISPLAY
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    st.write(regime)
    st.write(f"Score: {latest['SCORE']}")

with col2:
    st.subheader("Allocation")
    st.write(allocation)

# =========================
# CHART
# =========================
st.subheader("Market Trend")
st.line_chart(weekly)
