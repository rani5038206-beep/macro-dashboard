import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

# =========================
# BULK DATA DOWNLOAD (SAFE)
# =========================
@st.cache_data(ttl=3600)
def load_data():
    tickers = {
        "SPX": "^GSPC",
        "DXY": "DX-Y.NYB",
        "VIX": "^VIX",
        "US10Y": "^TNX",
        "NIFTY": "^NSEI",
        "BANK": "^NSEBANK",
        "IT": "^CNXIT"
    }

    try:
        raw = yf.download(
            list(tickers.values()),
            start=start,
            group_by="ticker",
            auto_adjust=True,
            progress=False
        )

        data = {}

        for name, ticker in tickers.items():
            try:
                data[name] = raw[ticker]["Close"]
            except:
                pass

        if len(data) == 0:
            return None

        df = pd.concat(data.values(), axis=1)
        df.columns = data.keys()
        df = df.ffill().dropna()

        return df

    except:
        return None


df = load_data()

if df is None:
    st.error("❌ Data not loading. Try again later.")
    st.stop()

# =========================
# WEEKLY DATA
# =========================
weekly = df.resample("W").last()

# =========================
# MACRO SIGNALS (STRONG)
# =========================
signal = pd.DataFrame(index=weekly.index)

signal["SPX"] = np.where(weekly["SPX"] > weekly["SPX"].rolling(20).mean(), 1, -1)
signal["DXY"] = np.where(weekly["DXY"] > weekly["DXY"].rolling(20).mean(), -2, 2)
signal["VIX"] = np.where(weekly["VIX"] > weekly["VIX"].rolling(20).mean(), -3, 3)
signal["US10Y"] = np.where(weekly["US10Y"] > weekly["US10Y"].rolling(20).mean(), -2, 2)

# =========================
# MOMENTUM (INDIA)
# =========================
mom = pd.DataFrame(index=weekly.index)

mom["NIFTY"] = np.where(weekly["NIFTY"].pct_change(12) > 0, 2, -2)
mom["BANK"] = np.where(weekly["BANK"].pct_change(12) > 0, 1, -1)
mom["IT"] = np.where(weekly["IT"].pct_change(12) > 0, 1, -1)

# =========================
# FINAL SCORE (MACRO DOMINANT)
# =========================
macro_score = signal.sum(axis=1)
momentum_score = mom.sum(axis=1)

final_score = (macro_score * 2) + momentum_score

latest_score = final_score.iloc[-1]

# =========================
# REGIME
# =========================
if latest_score >= 3:
    regime = "RISK ON"
elif latest_score <= -3:
    regime = "RISK OFF"
else:
    regime = "TRANSITION"

# =========================
# ALLOCATION
# =========================
if regime == "RISK ON":
    allocation = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
elif regime == "RISK OFF":
    allocation = {"Nifty": 10, "Bank": 10, "IT": 20, "Cash": 60}
else:
    allocation = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}

# =========================
# UI
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Regime")
    color = "🟢" if regime == "RISK ON" else "🔴" if regime == "RISK OFF" else "🟡"
    st.write(f"{color} {regime}")
    st.write(f"Score: {round(float(latest_score),2)}")

with col2:
    st.subheader("Allocation")
    st.json(allocation)

# =========================
# SIGNALS DISPLAY
# =========================
st.subheader("Macro Signals (Latest)")
st.dataframe(signal.tail(1))

# =========================
# CHART
# =========================
st.subheader("Market Trend")

chart_cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if chart_cols:
    st.line_chart(df[chart_cols])
else:
    st.warning("No chart data available")
