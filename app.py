import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

st.set_page_config(page_title="Client Dashboard", layout="wide")

FILE = "clients.json"

# =====================
# CLIENT STORAGE
# =====================
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

# =====================
# MARKET DATA
# =====================
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

latest = df.iloc[-1]
prev = df.iloc[-2]

signals = {
    "SPX": 1 if latest["SPX"] > prev["SPX"] else -1,
    "DXY": -1 if latest["DXY"] > prev["DXY"] else 1,
    "VIX": -1 if latest["VIX"] > prev["VIX"] else 1,
    "US10Y": -1 if latest["US10Y"] > prev["US10Y"] else 1,
}

score = int(sum(signals.values()))

# =====================
# REGIME LOGIC
# =====================
if score >= 2:
    regime = "RISK ON"
    model_equity = 70
    screener_link = "https://www.screener.in/screens/1929320/"
    screener_name = "Aggressive Growth Stocks"

elif score <= -2:
    regime = "RISK OFF"
    model_equity = 30
    screener_link = "https://www.screener.in/screens/1929322/"
    screener_name = "Defensive Stocks"

else:
    regime = "TRANSITION"
    model_equity = 50
    screener_link = "https://www.screener.in/screens/1929318/"
    screener_name = "Balanced Quality Stocks"

model_cash = 100 - model_equity

# =====================
# SIDEBAR
# =====================
st.sidebar.header("Client Management")

client_list = list(clients.keys())
selected = st.sidebar.selectbox("Select Client", ["New Client"] + client_list)

name = ""
equity = 60
value = 1000000

if selected == "New Client":
    name = st.sidebar.text_input("Client Name")
    equity = st.sidebar.slider("Equity %", 0, 100, 60)
    value = st.sidebar.number_input("Portfolio Value", value=1000000)

    if st.sidebar.button("Save Client"):
        if name.strip() != "":
            clients[name] = {"equity": equity, "value": value}
            save_clients(clients)
            st.sidebar.success("Saved")

else:
    data = clients[selected]
    name = selected
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

# =====================
# HEADER
# =====================
st.title(f"{name} - Portfolio Dashboard" if name else "Client Dashboard")

# =====================
# METRICS
# =====================
c1, c2, c3 = st.columns(3)
c1.metric("Market Regime", regime)
c2.metric("Model Score", score)
c3.metric("Last Updated", datetime.today().strftime("%d %b %Y"))

# =====================
# ACTION
# =====================
st.subheader("Action Required")

difference = model_equity - equity
amount_shift = abs(difference) * value / 100

if difference > 0:
    st.success(f"Increase Equity by {difference}%")
    st.write(f"Move ₹{int(amount_shift):,} from Cash to Equity")

elif difference < 0:
    st.error(f"Reduce Equity by {abs(difference)}%")
    st.write(f"Move ₹{int(amount_shift):,} from Equity to Cash/Debt")

else:
    st.info("No change required")

# =====================
# IMPACT
# =====================
st.subheader("Portfolio Impact")

current_equity_amt = value * (equity / 100)
model_equity_amt = value * (model_equity / 100)

col1, col2 = st.columns(2)
col1.metric("Current Equity", f"₹{int(current_equity_amt):,}")
col2.metric("Recommended Equity", f"₹{int(model_equity_amt):,}")

# =====================
# ADVISORY
# =====================
st.subheader
