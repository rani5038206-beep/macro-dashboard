import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ======================
# HEADER
# ======================
st.title("📊 Caring Click - Client Macro Dashboard")
st.caption("Client-specific asset allocation & advisory system")

START = "2018-01-01"

# ======================
# DATA LOAD
# ======================
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

    raw = yf.download(
        list(tickers.values()),
        start=START,
        group_by="ticker",
        auto_adjust=True,
        progress=False
    )

    data = {}
    for k, v in tickers.items():
        try:
            data[k] = raw[v]["Close"]
        except:
            continue

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()

    df = df.ffill().dropna()
    df.index = pd.to_datetime(df.index)

    return df


df = load_data()

if df is None or df.empty:
    st.error("⚠️ Data not available")
    st.stop()

# ======================
# WEEKLY
# ======================
weekly = df.resample("W").last()

# ======================
# SIGNALS
# ======================
def signal(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, 1, -1)

def inverse_signal(series):
    ma = series.rolling(20).mean()
    return np.where(series > ma, -1, 1)

def momentum(series):
    return np.where(series.pct_change(12) > 0, 1, -1)

sig = pd.DataFrame(index=weekly.index)

if "SPX" in weekly:
    sig["SPX"] = signal(weekly["SPX"])
if "DXY" in weekly:
    sig["DXY"] = inverse_signal(weekly["DXY"])
if "VIX" in weekly:
    sig["VIX"] = inverse_signal(weekly["VIX"])
if "US10Y" in weekly:
    sig["US10Y"] = inverse_signal(weekly["US10Y"])

mom = pd.DataFrame(index=weekly.index)

for col in ["NIFTY", "BANK", "IT"]:
    if col in weekly:
        mom[col] = momentum(weekly[col])

score = (sig.sum(axis=1) * 2) + mom.sum(axis=1)
latest_score = float(score.iloc[-1])

# ======================
# REGIME
# ======================
if latest_score >= 3:
    regime, color = "RISK ON", "🟢"
elif latest_score <= -3:
    regime, color = "RISK OFF", "🔴"
else:
    regime, color = "TRANSITION", "🟡"

# ======================
# MODEL ALLOCATION
# ======================
if latest_score >= 6:
    model_alloc = {"Nifty": 60, "Bank": 25, "IT": 15, "Cash": 0}
elif latest_score >= 3:
    model_alloc = {"Nifty": 50, "Bank": 30, "IT": 20, "Cash": 0}
elif latest_score >= 0:
    model_alloc = {"Nifty": 30, "Bank": 30, "IT": 20, "Cash": 20}
elif latest_score >= -3:
    model_alloc = {"Nifty": 20, "Bank": 20, "IT": 20, "Cash": 40}
else:
    model_alloc = {"Nifty": 10, "Bank": 10, "IT": 20, "Cash": 60}

# ======================
# CLIENT INPUT
# ======================
st.sidebar.header("👤 Client Portfolio")

client_equity = st.sidebar.slider("Equity %", 0, 100, 60)
client_cash = st.sidebar.slider("Cash %", 0, 100, 20)
client_other = 100 - (client_equity + client_cash)

# ======================
# CLIENT VS MODEL
# ======================
st.subheader("📌 Market Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Regime", f"{color} {regime}")

with col2:
    st.metric("Model Score", f"{latest_score:.1f}")

with col3:
    st.metric("Last Updated", df.index[-1].strftime("%Y-%m-%d"))

# ======================
# COMPARISON
# ======================
st.subheader("⚖️ Portfolio Comparison")

comparison = pd.DataFrame({
    "Model": [
        model_alloc["Nifty"] + model_alloc["Bank"] + model_alloc["IT"],
        model_alloc["Cash"]
    ],
    "Client": [
        client_equity,
        client_cash
    ]
}, index=["Equity", "Cash"])

st.bar_chart(comparison)

# ======================
# ACTION ENGINE (KEY)
# ======================
st.subheader("🚨 Action Required")

model_equity = model_alloc["Nifty"] + model_alloc["Bank"] + model_alloc["IT"]

diff = client_equity - model_equity

if diff > 10:
    action = "🔻 Reduce Equity Exposure"
elif diff < -10:
    action = "🔺 Increase Equity Exposure"
else:
    action = "✅ Maintain Current Allocation"

st.success(action)

# ======================
# DETAILED ADVICE
# ======================
st.subheader("📢 Advisory")

if regime == "RISK ON":
    msg = "Aggressive positioning allowed. Focus on growth sectors."
elif regime == "RISK OFF":
    msg = "Protect capital. Increase cash and defensive allocation."
else:
    msg = "Mixed signals. Maintain balanced allocation."

st.info(msg)

# ======================
# MODEL ALLOCATION
# ======================
st.subheader("📊 Recommended Allocation")

alloc_df = pd.DataFrame(list(model_alloc.items()), columns=["Asset", "Weight"])
st.bar_chart(alloc_df.set_index("Asset"))

# ======================
# SIGNALS
# ======================
st.subheader("🧠 Macro Signals")

latest = sig.tail(1).T
latest.columns = ["Signal"]
st.dataframe(latest)

# ======================
# TREND
# ======================
st.subheader("📈 Market Trend")

cols = [c for c in ["NIFTY", "BANK", "IT"] if c in df.columns]
st.line_chart(df[cols])

# ======================
# WHATSAPP REPORT
# ======================
st.subheader("📲 Client Report")

report = f"""
Market: {regime}
Score: {latest_score}

Model Allocation:
Nifty {model_alloc['Nifty']}%
Bank {model_alloc['Bank']}%
IT {model_alloc['IT']}%
Cash {model_alloc['Cash']}%

Client Equity: {client_equity}%
Recommended Action: {action}
"""

st.code(report)

# ======================
# FOOTER
# ======================
st.markdown("---")
st.caption("For advisory use only")
