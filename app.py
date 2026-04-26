import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

# =========================
# DATA LOADER
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

            time.sleep(1)  # avoid Yahoo rate limit

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
# SIGNALS (NO NaN)
# =========================
signals = {}

if "DXY" in weekly:
    ma = weekly["DXY"].rolling(20).mean()
    signals["DXY"] = np.where(weekly["DXY"] > ma, -1, 1)

if "SPX" in weekly:
    ma = weekly["SPX"].rolling(20).mean()
    signals["SPX"] = np.where(weekly["SPX"] > ma, 1, -1)

if "VIX" in weekly:
    ma = weekly["VIX"].rolling(10).mean()
    signals["VIX"] = np.where(weekly["VIX"] > ma, -1, 1)

if "US10Y" in weekly:
    ma = weekly["US10Y"].rolling(20).mean()
    signals["US10Y"] = np.where(weekly["US10Y"] > ma, -1, 1)

signal_df = pd.DataFrame(signals)

# =========================
# SCORE (WEIGHTED FIX)
# =========================
if signal_df.empty:
    weekly["SCORE"] = 0
else:
    signal_df = signal_df.fillna(0)

    weights = {
        "DXY": -2,
        "SPX": 2,
        "VIX": -2,
        "US10Y": -1
    }

    score = pd.Series(0, index=signal_df.index)

    for col in signal_df.columns:
        score += signal_df[col] * weights.get(col, 0)

    weekly["SCORE"] = score

latest = weekly.iloc[-1]

if pd.isna(latest["SCORE"]):
    latest["SCORE"] = 0

# =========================
# REGIME LOGIC (IMPROVED)
# =========================
if latest["SCORE"] <= -3:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":10,"Bank":0,"IT":60,"Cash":30}

elif latest["SCORE"] < 2:
    regime = "🟡 NEUTRAL"
    allocation = {"Nifty":30,"Bank":30,"IT":30,"Cash":10}

else:
    regime = "🟢 RISK ON"
    allocation = {"Nifty":60,"Bank":30,"IT":10,"Cash":0}

# =========================
# UI
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    st.write(regime)
    st.write(f"Score: {round(latest['SCORE'],2)}")

with col2:
    st.subheader("Allocation")
    st.write(allocation)

# =========================
# CHART
# =========================
st.subheader("Market Trend")
st.line_chart(weekly)
