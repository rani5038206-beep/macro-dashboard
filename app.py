import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import os

st.set_page_config(page_title="Client Dashboard", layout="wide")

DATA_FILE = "clients.csv"

# ---------------------------
# INIT CLIENT DATABASE
# ---------------------------
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Name", "Equity", "Value"])
    df_init.to_csv(DATA_FILE, index=False)

clients_df = pd.read_csv(DATA_FILE)

# ---------------------------
# LOAD MARKET DATA
# ---------------------------
@st.cache_data(ttl=3600)
def load_data():
    tickers = {
        "SPX": "^GSPC",
        "DXY": "DX-Y.NYB",
        "VIX": "^VIX",
        "US10Y": "^TNX"
    }

    data = {}

    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if not df.empty:
                data[name] = df["Close"]
        except:
            pass

    if len(data) == 0:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    return df.dropna()


df = load_data()

if df is None:
    st.error("❌ Data not loading")
    st.stop()

# ---------------------------
# SIGNAL ENGINE
# ---------------------------
weekly = df.resample("W").last()

for col in weekly.columns:
    weekly[f"{col}_S"] = np.where(
        weekly[col] > weekly[col].rolling(20).mean(), 1, -1
    )

latest = weekly.iloc[-1]

score = (
    latest["SPX_S"]
    - latest["DXY_S"]
    - latest["VIX_S"]
    - latest["US10Y_S"]
)

# ---------------------------
# REGIME
# ---------------------------
if score >= 2:
    regime = "RISK ON"
    color = "🟢"
    allocation = {"Equity": 80, "Cash": 20}
    message = "Increase equity exposure"
elif score <= -2:
    regime = "RISK OFF"
    color = "🔴"
    allocation = {"Equity": 40, "Cash": 60}
    message = "Reduce equity exposure"
else:
    regime = "TRANSITION"
    color = "🟡"
    allocation = {"Equity": 60, "Cash": 40}
    message = "Maintain balanced allocation"

# ---------------------------
# SIDEBAR - CLIENT MGMT
# ---------------------------
st.sidebar.header("👤 Client Management")

client_names = clients_df["Name"].tolist()

selected_client = st.sidebar.selectbox(
    "Select Client",
    ["New Client"] + client_names
)

if selected_client == "New Client":
    name = st.sidebar.text_input("Client Name")
    equity = st.sidebar.slider("Equity %", 0, 100, 60)
    value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

    if st.sidebar.button("Save Client"):
        new_row = pd.DataFrame([[name, equity, value]],
                               columns=["Name", "Equity", "Value"])
        clients_df = pd.concat([clients_df, new_row])
        clients_df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("Client Saved")
else:
    row = clients_df[clients_df["Name"] == selected_client].iloc[0]
    name = row["Name"]
    equity = int(row["Equity"])
    value = int(row["Value"])

cash = 100 - equity

# ---------------------------
# HEADER
# ---------------------------
st.title(f"📊 {name} - Portfolio Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Regime", f"{color} {regime}")
col2.metric("Score", f"{score:.1f}")
col3.metric("Updated", df.index[-1].strftime("%d %b %Y"))

# ---------------------------
# ADVISORY
# ---------------------------
st.subheader("📢 Advisory")

if "Increase" in message:
    st.success(message)
elif "Reduce" in message:
    st.error(message)
else:
    st.warning(message)

# ---------------------------
# COMPARISON
# ---------------------------
st.subheader("⚖️ Portfolio Comparison")

client_alloc = {"Equity": equity, "Cash": cash}
model_alloc = allocation

comparison = pd.DataFrame({
    "Client": client_alloc,
    "Model": model_alloc
})

st.bar_chart(comparison.T)

# ---------------------------
# ACTION
# ---------------------------
st.subheader("🚨 Action")

diff = model_alloc["Equity"] - equity
amount = value * abs(diff) / 100

if diff > 10:
    st.success(f"BUY ₹ {int(amount):,}")
elif diff < -10:
    st.error(f"SELL ₹ {int(amount):,}")
else:
    st.info("HOLD")

# ---------------------------
# SIGNALS
# ---------------------------
st.subheader("🧠 Macro Signals")

signals = pd.DataFrame({
    "Indicator": ["SPX", "DXY", "VIX", "US10Y"],
    "Signal": [
        latest["SPX_S"],
        latest["DXY_S"],
        latest["VIX_S"],
        latest["US10Y_S"]
    ]
})

st.table(signals)

# ---------------------------
# TREND
# ---------------------------
st.subheader("📈 Market Trend")

st.line_chart(df)

# ---------------------------
# FOOTER
# ---------------------------
st.caption("For informational purposes only.")
