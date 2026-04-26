import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import os
import uuid

st.set_page_config(page_title="Client Dashboard", layout="wide")

DATA_FILE = "clients.csv"

# ---------------------------
# INIT DATABASE
# ---------------------------
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["ID", "Name", "Equity", "Value"]).to_csv(DATA_FILE, index=False)

clients_df = pd.read_csv(DATA_FILE)

def save_clients(df):
    df.to_csv(DATA_FILE, index=False)

# ---------------------------
# REMOVE DUPLICATES (SAFE)
# ---------------------------
clients_df = clients_df.drop_duplicates(subset=["Name"], keep="last")
save_clients(clients_df)

# ---------------------------
# MARKET DATA
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
    for k, v in tickers.items():
        try:
            d = yf.download(v, period="1y", progress=False)
            if not d.empty:
                data[k] = d["Close"]
        except:
            pass

    if len(data) == 0:
        return None

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    return df.dropna()

df = load_data()

if df is None:
    st.error("❌ Market data unavailable")
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
# REGIME LOGIC
# ---------------------------
if score >= 2:
    regime = "RISK ON"
    color = "🟢"
    model_alloc = {"Equity": 80, "Cash": 20}
    message = "Increase equity exposure"
elif score <= -2:
    regime = "RISK OFF"
    color = "🔴"
    model_alloc = {"Equity": 40, "Cash": 60}
    message = "Reduce equity exposure"
else:
    regime = "TRANSITION"
    color = "🟡"
    model_alloc = {"Equity": 60, "Cash": 40}
    message = "Maintain balanced allocation"

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.header("👤 Client Management")

client_names = clients_df["Name"].tolist()
selected_name = st.sidebar.selectbox("Select Client", ["➕ New Client"] + client_names)

# ---------------------------
# NEW CLIENT
# ---------------------------
if selected_name == "➕ New Client":
    st.title("➕ Create New Client")

    name = st.text_input("Client Name")
    equity = st.slider("Equity %", 0, 100, 60)
    value = st.number_input("Portfolio Value (₹)", value=1000000)

    if st.button("Save Client"):

        if name.strip() == "":
            st.error("⚠️ Enter client name")

        else:
            if name in clients_df["Name"].values:
                clients_df.loc[clients_df["Name"] == name, ["Equity", "Value"]] = [equity, value]
                st.success("✅ Client updated")
            else:
                new_id = str(uuid.uuid4())[:8]
                new = pd.DataFrame([[new_id, name, equity, value]],
                                   columns=["ID", "Name", "Equity", "Value"])
                clients_df = pd.concat([clients_df, new], ignore_index=True)
                st.success("✅ Client added")

            save_clients(clients_df)
            st.session_state["client"] = name
            st.rerun()

    st.stop()

# ---------------------------
# REDIRECT
# ---------------------------
if "client" in st.session_state:
    selected_name = st.session_state["client"]

# ---------------------------
# LOAD CLIENT
# ---------------------------
row = clients_df[clients_df["Name"] == selected_name].iloc[0]

name = row["Name"]
equity = st.sidebar.slider("Equity %", 0, 100, int(row["Equity"]))
value = st.sidebar.number_input("Portfolio Value (₹)", value=int(row["Value"]))

col1, col2 = st.sidebar.columns(2)

if col1.button("Update"):
    clients_df.loc[clients_df["Name"] == name, ["Equity", "Value"]] = [equity, value]
    save_clients(clients_df)
    st.sidebar.success("Updated")

if col2.button("Delete"):
    clients_df = clients_df[clients_df["Name"] != name]
    save_clients(clients_df)
    st.sidebar.warning("Deleted")
    st.rerun()

cash = 100 - equity

# ---------------------------
# DASHBOARD
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
# PORTFOLIO COMPARISON
# ---------------------------
st.subheader("⚖️ Portfolio Comparison")

client_alloc = {"Equity": equity, "Cash": cash}

comparison = pd.DataFrame({
    "Client": client_alloc,
    "Model": model_alloc
})

st.bar_chart(comparison.T)

# ---------------------------
# ACTION ENGINE
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

st.table(pd.DataFrame({
    "Indicator": ["SPX", "DXY", "VIX", "US10Y"],
    "Signal": [
        latest["SPX_S"],
        latest["DXY_S"],
        latest["VIX_S"],
        latest["US10Y_S"]
    ]
}))

# ---------------------------
# MARKET TREND
# ---------------------------
st.subheader("📈 Market Trend")
st.line_chart(df)

# ---------------------------
# FOOTER
# ---------------------------
st.caption("For informational purposes only")
