import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 Caring Click - Macro Allocation Dashboard")
st.caption("Model-driven asset allocation | For client communication")

start = "2018-01-01"

# =========================
# DATA LOADING (STABLE)
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
    st.error("⚠️ Data temporarily unavailable. Please check later.")
    st.stop()

# =========================
# WEEKLY DATA
# =========================
weekly = df.resample("W").last()

# =========================
# MACRO SIGNALS
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
# FINAL SCORE
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
    color = "🟢"
elif latest_score <= -3:
    regime = "RISK OFF"
    color = "🔴"
else:
    regime = "TRANSITION"
    color = "🟡"

# =========================
# CLIENT-FRIENDLY ALLOCATION
# =========================
if latest_score >= 6:
    allocation = {"Nifty": 60, "Bank": 25, "IT": 15, "Cash": 0}
    message = "Strong positive environment. Higher equity allocation recommended."
elif latest_score >= 3:
    allocation = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
    message = "Positive trend. Maintain equity exposure."
elif latest_score >= 0:
    allocation = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}
    message = "Mixed signals. Balanced approach advised."
elif latest_score >= -3:
    allocation = {"Nifty": 20, "Bank": 20, "IT": 20, "Cash": 40}
    message = "Weak conditions. Reduce risk exposure."
else:
    allocation = {"Nifty": 10, "Bank": 10, "IT": 20, "Cash": 60}
    message = "High risk environment. Preserve capital."

# =========================
# TOP SECTION (CLIENT VIEW)
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Regime", f"{color} {regime}")

with col2:
    st.metric("Model Score", round(float(latest_score), 2))

with col3:
    st.metric("Last Updated", df.index[-1].date())

st.info(f"📌 Advisory View: {message}")

# =========================
# ALLOCATION
# =========================
st.subheader("📊 Recommended Allocation")

alloc_df = pd.DataFrame(list(allocation.items()), columns=["Asset", "Weight"])
st.bar_chart(alloc_df.set_index("Asset"))

# =========================
# SIGNAL BREAKDOWN
# =========================
st.subheader("🧠 Macro Signals (Latest)")

latest_signals = signal.tail(1).T
latest_signals.columns = ["Signal"]

def signal_label(x):
    if x > 0:
        return "Positive"
    elif x < 0:
        return "Negative"
    else:
        return "Neutral"

latest_signals["Interpretation"] = latest_signals["Signal"].apply(signal_label)

st.dataframe(latest_signals)

# =========================
# MARKET TREND
# =========================
st.subheader("📈 Market Trend")

chart_cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if chart_cols:
    st.line_chart(df[chart_cols])
else:
    st.warning("Chart data unavailable")

# =========================
# FOOTER (IMPORTANT)
# =========================
st.markdown("---")
st.caption("This model is for informational purposes only. Not investment advice.")
