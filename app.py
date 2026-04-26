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

            time.sleep(1)

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
# STRONG SIGNAL ENGINE
# =========================
signals = {}

def trend_signal(series, short=4, long=20):
    ma_short = series.rolling(short).mean()
    ma_long = series.rolling(long).mean()
    return np.where(ma_short > ma_long, 1, -1)

if "SPX" in weekly:
    signals["SPX"] = trend_signal(weekly["SPX"])

if "DXY" in weekly:
    signals["DXY"] = -trend_signal(weekly["DXY"])

if "VIX" in weekly:
    signals["VIX"] = -trend_signal(weekly["VIX"], short=2, long=10)

if "US10Y" in weekly:
    signals["US10Y"] = -trend_signal(weekly["US10Y"])

signal_df = pd.DataFrame(signals).fillna(0)

# =========================
# MOMENTUM BOOST (KEY FIX)
# =========================
momentum = {}

if "NIFTY" in weekly:
    momentum["NIFTY"] = np.sign(weekly["NIFTY"].pct_change(4))

if "BANK" in weekly:
    momentum["BANK"] = np.sign(weekly["BANK"].pct_change(4))

mom_df = pd.DataFrame(momentum).fillna(0)

# =========================
# FINAL SCORE (POWERFUL)
# =========================
score = signal_df.sum(axis=1) * 2 + mom_df.sum(axis=1)

weekly["SCORE"] = score

latest = weekly.iloc[-1]

if pd.isna(latest["SCORE"]):
    latest["SCORE"] = 0

# =========================
# REGIME (MORE SENSITIVE)
# =========================
if latest["SCORE"] <= -4:
    regime = "🔴 RISK OFF"
    allocation = {"Nifty":10,"Bank":0,"IT":60,"Cash":30}

elif latest["SCORE"] <= 1:
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
# SIGNAL VIEW (IMPORTANT)
# =========================
st.subheader("Macro Signals")
st.write(signal_df.tail(1))

# =========================
# CHART
# =========================
st.subheader("Market Trend")
st.line_chart(weekly)
