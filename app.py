import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# =====================
# HEADER
# =====================
st.title("📊 Caring Click - Macro Allocation Dashboard")
st.caption("Model-driven asset allocation | For client communication")

START = "2018-01-01"

# =====================
# DATA LOADING
# =====================
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
            start=START,
            group_by="ticker",
            auto_adjust=True,
            progress=False
        )
    except:
        return None

    data = {}
    for k, v in tickers.items():
        try:
            data[k] = raw[v]["Close"]
        except:
            continue

    if not data:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()

    df = df.ffill().dropna()

    # ✅ FORCE datetime (critical)
    df.index = pd.to_datetime(df.index)

    return df


df = load_data()

if df is None or df.empty:
    st.error("⚠️ Data not available. Try later.")
    st.stop()

# =====================
# WEEKLY DATA
# =====================
weekly = df.resample("W").last()

# =====================
# SIGNALS
# =====================
def signal(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, 1, -1)

def signal_inverse(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, -1, 1)

def momentum(series):
    return np.where(series.pct_change(12) > 0, 1, -1)

sig = pd.DataFrame(index=weekly.index)

if "SPX" in weekly:
    sig["SPX"] = signal(weekly["SPX"])
if "DXY" in weekly:
    sig["DXY"] = signal_inverse(weekly["DXY"])
if "VIX" in weekly:
    sig["VIX"] = signal_inverse(weekly["VIX"])
if "US10Y" in weekly:
    sig["US10Y"] = signal_inverse(weekly["US10Y"])

mom = pd.DataFrame(index=weekly.index)

for col in ["NIFTY", "BANK", "IT"]:
    if col in weekly:
        mom[col] = momentum(weekly[col])

# =====================
# SCORE
# =====================
score = (sig.sum(axis=1) * 2) + mom.sum(axis=1)
latest_score = float(score.iloc[-1])

# =====================
# REGIME
# =====================
if latest_score >= 3:
    regime, color = "RISK ON", "🟢"
elif latest_score <= -3:
    regime, color = "RISK OFF", "🔴"
else:
    regime, color = "TRANSITION", "🟡"

# =====================
# ALLOCATION
# =====================
if latest_score >= 6:
    alloc = {"Nifty": 60, "Bank": 25, "IT": 15, "Cash": 0}
    msg = "Strong positive environment."
elif latest_score >= 3:
    alloc = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
    msg = "Positive trend."
elif latest_score >= 0:
    alloc = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}
    msg = "Balanced approach."
elif latest_score >= -3:
    alloc = {"Nifty": 20, "Bank": 20, "IT": 20, "Cash": 40}
    msg = "Reduce exposure."
else:
    alloc = {"Nifty": 10, "Bank": 10, "IT": 20, "Cash": 60}
    msg = "Capital protection."

# =====================
# METRICS (FINAL FIX)
# =====================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Regime", f"{color} {regime}")

with col2:
    st.metric("Model Score", f"{latest_score:.1f}")

with col3:
    # 🔥 HARD FIX → ALWAYS STRING
    last_date = df.index[-1].strftime("%Y-%m-%d")
    st.metric("Last Updated", last_date)

st.info(f"📌 Advisory View: {msg}")

# =====================
# ALLOCATION CHART
# =====================
st.subheader("📊 Recommended Allocation")

alloc_df = pd.DataFrame(list(alloc.items()), columns=["Asset", "Weight"])
st.bar_chart(alloc_df.set_index("Asset"))

# =====================
# SIGNAL TABLE
# =====================
st.subheader("🧠 Macro Signals (Latest)")

latest = sig.tail(1).T
latest.columns = ["Signal"]
st.dataframe(latest)

# =====================
# TREND
# =====================
st.subheader("📈 Market Trend")

cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if cols:
    st.line_chart(df[cols])
else:
    st.warning("No chart data available")

# =====================
# FOOTER
# =====================
st.markdown("---")
st.caption("For informational purposes only.")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# =====================
# HEADER
# =====================
st.title("📊 Caring Click - Macro Allocation Dashboard")
st.caption("Model-driven asset allocation | For client communication")

START = "2018-01-01"

# =====================
# DATA LOADING
# =====================
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
            start=START,
            group_by="ticker",
            auto_adjust=True,
            progress=False
        )
    except:
        return None

    data = {}
    for k, v in tickers.items():
        try:
            data[k] = raw[v]["Close"]
        except:
            continue

    if not data:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()

    df = df.ffill().dropna()

    # ✅ FORCE datetime (critical)
    df.index = pd.to_datetime(df.index)

    return df


df = load_data()

if df is None or df.empty:
    st.error("⚠️ Data not available. Try later.")
    st.stop()

# =====================
# WEEKLY DATA
# =====================
weekly = df.resample("W").last()

# =====================
# SIGNALS
# =====================
def signal(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, 1, -1)

def signal_inverse(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, -1, 1)

def momentum(series):
    return np.where(series.pct_change(12) > 0, 1, -1)

sig = pd.DataFrame(index=weekly.index)

if "SPX" in weekly:
    sig["SPX"] = signal(weekly["SPX"])
if "DXY" in weekly:
    sig["DXY"] = signal_inverse(weekly["DXY"])
if "VIX" in weekly:
    sig["VIX"] = signal_inverse(weekly["VIX"])
if "US10Y" in weekly:
    sig["US10Y"] = signal_inverse(weekly["US10Y"])

mom = pd.DataFrame(index=weekly.index)

for col in ["NIFTY", "BANK", "IT"]:
    if col in weekly:
        mom[col] = momentum(weekly[col])

# =====================
# SCORE
# =====================
score = (sig.sum(axis=1) * 2) + mom.sum(axis=1)
latest_score = float(score.iloc[-1])

# =====================
# REGIME
# =====================
if latest_score >= 3:
    regime, color = "RISK ON", "🟢"
elif latest_score <= -3:
    regime, color = "RISK OFF", "🔴"
else:
    regime, color = "TRANSITION", "🟡"

# =====================
# ALLOCATION
# =====================
if latest_score >= 6:
    alloc = {"Nifty": 60, "Bank": 25, "IT": 15, "Cash": 0}
    msg = "Strong positive environment."
elif latest_score >= 3:
    alloc = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
    msg = "Positive trend."
elif latest_score >= 0:
    alloc = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}
    msg = "Balanced approach."
elif latest_score >= -3:
    alloc = {"Nifty": 20, "Bank": 20, "IT": 20, "Cash": 40}
    msg = "Reduce exposure."
else:
    alloc = {"Nifty": 10, "Bank": 10, "IT": 20, "Cash": 60}
    msg = "Capital protection."

# =====================
# METRICS (FINAL FIX)
# =====================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Regime", f"{color} {regime}")

with col2:
    st.metric("Model Score", f"{latest_score:.1f}")

with col3:
    # 🔥 HARD FIX → ALWAYS STRING
    last_date = df.index[-1].strftime("%Y-%m-%d")
    st.metric("Last Updated", last_date)

st.info(f"📌 Advisory View: {msg}")

# =====================
# ALLOCATION CHART
# =====================
st.subheader("📊 Recommended Allocation")

alloc_df = pd.DataFrame(list(alloc.items()), columns=["Asset", "Weight"])
st.bar_chart(alloc_df.set_index("Asset"))

# =====================
# SIGNAL TABLE
# =====================
st.subheader("🧠 Macro Signals (Latest)")

latest = sig.tail(1).T
latest.columns = ["Signal"]
st.dataframe(latest)

# =====================
# TREND
# =====================
st.subheader("📈 Market Trend")

cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]

if cols:
    st.line_chart(df[cols])
else:
    st.warning("No chart data available")

# =====================
# FOOTER
# =====================
st.markdown("---")
st.caption("For informational purposes only.")
