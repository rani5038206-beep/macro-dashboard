import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# STORAGE
# =========================
FILE = "clients.json"

def load_clients():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_clients(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

clients = load_clients()

# =========================
# DATA (SAFE)
# =========================
@st.cache_data(ttl=600)
def get_data():
    try:
        df = yf.download(
            ["^GSPC", "DX-Y.NYB", "^VIX", "^TNX"],
            period="6mo",
            progress=False
        )["Close"].dropna()

        df.columns = ["SPX", "DXY", "VIX", "US10Y"]
        return df
    except:
        dates = pd.date_range(end=datetime.today(), periods=100)
        return pd.DataFrame({
            "SPX": np.random.rand(100)*1000+4000,
            "DXY": np.random.rand(100)*10+95,
            "VIX": np.random.rand(100)*5+15,
            "US10Y": np.random.rand(100)+3
        }, index=dates)

df = get_data()

# =========================
# SIGNAL ENGINE
# =========================
latest = df.iloc[-1]
prev = df.iloc[-2]

signals = {
    "SPX": 1 if latest["SPX"] > prev["SPX"] else -1,
    "DXY": -1 if latest["DXY"] > prev["DXY"] else 1,
    "VIX": -1 if latest["VIX"] > prev["VIX"] else 1,
    "US10Y": -1 if latest["US10Y"] > prev["US10Y"] else 1,
}

score = int(sum(signals.values()))

# =========================
# REGIME
# =========================
if score >= 2:
    regime = "RISK ON"
    alloc = {"Equity": 70, "Cash": 30}
    advice = "Increase equity exposure"
elif score <= -2:
    regime = "RISK OFF"
    alloc = {"Equity": 30, "Cash": 70}
    advice = "Reduce equity exposure"
else:
    regime = "TRANSITION"
    alloc = {"Equity": 50, "Cash": 50}
    advice = "Balanced approach"

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Client Management")

client_names = list(clients.keys())
selected_client = st.sidebar.selectbox("Select Client", ["New Client"] + client_names)

# DEFAULT VALUES
name = ""
equity = 60
value = 1000000

if selected_client == "New Client":
    name = st.sidebar.text_input("Client Name")
    equity = st.sidebar.slider("Equity %", 0, 100, 60)
    value = st.sidebar.number_input("Portfolio Value", value=1000000)

    if st.sidebar.button("Save Client"):
        if name.strip() == "":
            st.sidebar.error("Client name required")
        else:
            clients[name] = {"equity": equity, "value": value}
            save_clients(clients)
            st.sidebar.success("Saved successfully")
else:
    data = clients[selected_client]
    name = selected_client
    equity = st.sidebar.slider("Equity %", 0, 100, data["equity"])
    value = st.sidebar.number_input("Portfolio Value", value=data["value"])

    if st.sidebar.button("Update"):
        clients[name] = {"equity": equity, "value": value}
        save_clients(clients)
        st.sidebar.success("Updated")

    if st.sidebar.button("Delete"):
        del clients[name]
        save_clients(clients)
        st.sidebar.warning("Deleted")

cash = 100 - equity

# =========================
# TITLE FIX (IMPORTANT)
# =========================
if name.strip() == "":
    st.title("Client Portfolio Dashboard")
else:
    st.title(f"{name} - Portfolio Dashboard")

# =========================
# METRICS
# =========================
c1, c2, c3 = st.columns(3)
c1.metric("Regime", regime)
c2.metric("Score", score)
c3.metric("Updated", datetime.today().strftime("%d %b %Y"))

# =========================
# ADVISORY
# =========================
st.subheader("Advisory")

if regime == "RISK ON":
    st.success(advice)
elif regime == "RISK OFF":
    st.error(advice)
else:
    st.warning(advice)

# =========================
# COMPARISON
# =========================
st.subheader("Portfolio Comparison")

df_compare = pd.DataFrame({
    "Client": [equity, cash],
    "Model": [alloc["Equity"], alloc["Cash"]]
}, index=["Equity", "Cash"])

st.bar_chart(df_compare)

# =========================
# TREND
# =========================
st.subheader("Market Trend")
st.line_chart(df)

# =========================
# SIGNAL TABLE
# =========================
st.subheader("Signals")
st.table(pd.DataFrame(signals, index=["Signal"]).T)

st.caption("For informational purposes only.")
