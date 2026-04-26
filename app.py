import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 Caring Click - Macro Allocation Dashboard")
st.caption("Model-driven asset allocation | For client communication")

START_DATE = "2018-01-01"

# =========================
# LOAD DATA (ROBUST)
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
            start=START_DATE,
            group_by="ticker",
            auto_adjust=True,
            progress=False
        )
    except:
        return None

    data = {}
    for name, ticker in tickers.items():
        try:
            series = raw[ticker]["Close"]
            if series is not None:
                data[name] = series
        except:
            pass

    if not data:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    df = df.ffill().dropna()

    return df


df = load_data()

if df is None or df.empty:
    st.error("⚠️ Data not available. Please refresh later.")
    st.stop()

# =========================
# WEEKLY DATA
# =========================
weekly = df.resample("W").last()

# =========================
# SIGNAL FUNCTIONS
# =========================
def safe_signal(series, invert=False):
    ma = series.rolling(20).mean()
    if invert:
        return np.where(series > ma, -1, 1)
    else:
        return np.where(series > ma, 1, -1)

def safe_momentum(series):
    return np.where(series.pct_change(12) > 0, 1, -1)

# =========================
# BUILD SIGNALS
# =========================
signal = pd.DataFrame(index=weekly.index)

for col in ["SPX", "DXY", "VIX", "US10Y"]:
    if col in weekly.columns:
        signal[col] = safe_signal(weekly[col], invert=(col != "SPX"))
    else:
        signal[col] = 0

mom = pd.DataFrame(index=weekly.index)

for col in ["NIFTY", "BANK", "IT"]:
    if col in weekly.columns:
        mom[col] = safe_momentum(weekly[col])
    else:
        mom[col] = 0

# =========================
# SCORE
# =========================
macro_score = signal.sum(axis=1)
momentum_score = mom.sum(axis=1)
final_score = (macro_score * 2) + momentum_score

latest_score = float(final_score.iloc[-1])

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
# ALLOCATION
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
# METRICS (FIXED)
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Regime", f"{color} {regime}")

with col2:
    st.metric("Model Score", f"{latest_score:.1f}")

with col3:
    last_date = df.index[-1]
    st.metric("Last Updated", last_date.strftime("%d %b %Y"))

st.info(f"📌 Advisory View: {message}")

# =========================
# ALLOCATION CHART
# =========================
st.subheader("📊 Recommended Allocation")

alloc_df = pd.DataFrame(list(allocation.items()), columns=["Asset", "Weight"])
st.bar_chart(alloc_df.set_index("Asset"))

# =========================
# SIGNAL TABLE
# =========================
st.subheader("🧠 Macro Signals (Latest)")

latest_signals = signal.tail(1).T
latest_signals.columns = ["Signal"]

st.dataframe(latest_signals)

# =========================
# MARKET TREND
# =========================
st.subheader("📈 Market Trend")

cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if cols:
    st.line_chart(df[cols])
else:
    st.warning("Chart data unavailable")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("For informational purposes only. Not investment advice.")
