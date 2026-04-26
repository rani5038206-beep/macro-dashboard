import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Macro Allocation Dashboard")

start = "2018-01-01"

# =========================
# BULK DATA DOWNLOAD (FIXED)
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
        failed = []

        for name, ticker in tickers.items():
            try:
                df = raw[ticker]
                if "Close" in df:
                    data[name] = df["Close"]
                else:
                    failed.append(name)
            except:
                failed.append(name)

        if len(data) == 0:
            return None, failed

        df = pd.concat(data.values(), axis=1)
        df.columns = data.keys()
        df = df.ffill().dropna()

        return df, failed

    except:
        return None, list(tickers.keys())


df, failed = load_data()

if df is None:
    st.error("❌ Data not loading. Try again later.")
    st.stop()

if failed:
    st.warning(f"⚠ Missing data: {failed}")

# =========================
# WEEKLY DATA
# =========================
weekly = df.resample("W").last()

# =========================
# MACRO SIGNALS
# =========================
signal_df = pd.DataFrame(index=weekly.index)

if "SPX" in weekly:
    signal_df["SPX"] = np.where(weekly["SPX"] > weekly["SPX"].rolling(20).mean(), 1, -1)

if "DXY" in weekly:
    signal_df["DXY"] = np.where(weekly["DXY"] > weekly["DXY"].rolling(20).mean(), -1, 1)

if "VIX" in weekly:
    signal_df["VIX"] = np.where(weekly["VIX"] > weekly["VIX"].rolling(20).mean(), -1, 1)

if "US10Y" in weekly:
    signal_df["US10Y"] = np.where(weekly["US10Y"] > weekly["US10Y"].rolling(20).mean(), -1, 1)

# =========================
# MOMENTUM (INDIA)
# =========================
mom_df = pd.DataFrame(index=weekly.index)

if "NIFTY" in weekly:
    mom_df["NIFTY"] = np.where(weekly["NIFTY"].pct_change(12) > 0, 1, -1)

if "BANK" in weekly:
    mom_df["BANK"] = np.where(weekly["BANK"].pct_change(12) > 0, 1, -1)

if "IT" in weekly:
    mom_df["IT"] = np.where(weekly["IT"].pct_change(12) > 0, 1, -1)

# =========================
# WEIGHTED SCORING
# =========================
weights = {
    "SPX": 2,
    "DXY": 3,
    "VIX": 3,
    "US10Y": 2
}

macro_score = pd.Series(0, index=weekly.index)

for col in signal_df.columns:
    macro_score += signal_df[col] * weights.get(col, 1)

momentum_score = mom_df.sum(axis=1) * 2

final_score = macro_score + momentum_score

latest_score = final_score.iloc[-1]

# =========================
# REGIME
# =========================
if latest_score > 2:
    regime = "RISK ON"
elif latest_score < -2:
    regime = "RISK OFF"
else:
    regime = "NEUTRAL"

# =========================
# ALLOCATION
# =========================
if regime == "RISK ON":
    allocation = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
elif regime == "RISK OFF":
    allocation = {"Nifty": 20, "Bank": 10, "IT": 20, "Cash": 50}
else:
    allocation = {"Nifty": 30, "Bank": 30, "IT": 30, "Cash": 10}

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
# SIGNAL DISPLAY
# =========================
st.subheader("Macro Signals (Latest)")
st.dataframe(signal_df.tail(1))

# =========================
# CHART
# =========================
st.subheader("Market Trend")

chart_cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if chart_cols:
    st.line_chart(df[chart_cols])
else:
    st.warning("No chart data available")
