import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Macro → Micro Portfolio Engine", layout="wide")

# ===============================
# SESSION STATE (CLIENT)
# ===============================
if "client" not in st.session_state:
    st.session_state.client = None

# ===============================
# STEP 1 → CLIENT CREATION
# ===============================
if st.session_state.client is None:

    st.title("Client Management")

    name = st.text_input("Client Name")
    portfolio = st.number_input("Portfolio Value (₹)", value=1000000)
    equity = st.slider("Equity %", 0, 100, 60)

    if st.button("Save Client"):
        if name.strip() == "":
            st.warning("Enter client name")
        else:
            st.session_state.client = {
                "name": name,
                "portfolio": portfolio,
                "equity": equity
            }
            st.success("Saved successfully")
            st.rerun()

    st.stop()

# ===============================
# CLIENT DATA
# ===============================
client = st.session_state.client
portfolio_value = client["portfolio"]
current_equity = client["equity"]

# ===============================
# SIDEBAR (CLEAN)
# ===============================
st.sidebar.header("Client Management")
st.sidebar.write(f"Client: {client['name']}")
st.sidebar.write(f"Portfolio: ₹{portfolio_value:,}")
st.sidebar.write(f"Equity: {current_equity}%")

# ===============================
# SAFE DOWNLOAD
# ===============================
def safe_download(ticker):
    try:
        df = yf.download(ticker, period="3mo", progress=False)
        if df.empty:
            return pd.Series(dtype=float)
        return df["Close"].dropna()
    except:
        return pd.Series(dtype=float)

# ===============================
# SIGNAL LOGIC (FIXED)
# ===============================
def get_signal(series):
    try:
        if len(series) < 20:
            return 0
        last = float(series.iloc[-1])
        prev = float(series.iloc[-20])
        return 1 if last > prev else -1
    except:
        return 0

# ===============================
# MACRO DATA (AUTO)
# ===============================
macro_data = {
    "SPX": safe_download("^GSPC"),
    "DXY": safe_download("DX-Y.NYB"),
    "INDIAVIX": safe_download("^INDIAVIX"),
    "USDINR": safe_download("INR=X"),
    "CRUDE": safe_download("CL=F"),
    "INDIA10Y": safe_download("^TNX")
}

signals = {k: get_signal(v) for k, v in macro_data.items()}

# ===============================
# INDIA IMPACT ALIGNMENT
# ===============================
signals["DXY"] *= -1
signals["INDIAVIX"] *= -1
signals["USDINR"] *= -1
signals["CRUDE"] *= -1
signals["INDIA10Y"] *= -1

# ===============================
# SCORE
# ===============================
weights = {
    "SPX": 0.2,
    "DXY": 0.2,
    "INDIAVIX": 0.15,
    "USDINR": 0.15,
    "CRUDE": 0.15,
    "INDIA10Y": 0.15
}

score_raw = sum(signals[k] * weights[k] for k in weights)
score_percent = round((score_raw + 1) * 50, 1)

# ===============================
# DECISION ENGINE
# ===============================
if score_percent >= 70:
    decision = "BUY"
    equity_alloc = 70
elif score_percent >= 51:
    decision = "HOLD"
    equity_alloc = 50
else:
    decision = "REDUCE"
    equity_alloc = 30

# ===============================
# HEADER
# ===============================
st.title(f"{client['name']} - Portfolio Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("India Score %", f"{score_percent}%")
col2.metric("Decision", decision)
col3.metric("Equity Allocation", f"{equity_alloc}%")

# ===============================
# ACTION (NEW FLOW)
# ===============================
st.subheader("Action Required")

diff = equity_alloc - current_equity

if abs(diff) < 5:
    st.success("HOLD - No major change")
elif diff > 0:
    amount = portfolio_value * diff / 100
    st.info(f"ADD ₹{int(amount):,} to Equity")
else:
    amount = portfolio_value * abs(diff) / 100
    st.error(f"REDUCE ₹{int(amount):,} from Equity")

# ===============================
# MACRO INTERPRETATION
# ===============================
def explain(k, s):
    mapping = {
        "SPX": "Global support" if s==1 else "Global weakness",
        "DXY": "Weak dollar → FII inflow" if s==1 else "Strong dollar → FII outflow",
        "INDIAVIX": "Low volatility → Stable market" if s==1 else "High volatility → Fear",
        "USDINR": "Strong INR → Positive" if s==1 else "Weak INR → Negative",
        "CRUDE": "Low crude → Low inflation" if s==1 else "High crude → Inflation risk",
        "INDIA10Y": "Low yield → Cheap capital" if s==1 else "High yield → Expensive capital"
    }
    return mapping.get(k, "")

rows = []
for k in signals:
    rows.append({
        "Factor": k,
        "Signal": signals[k],
        "Impact": "Positive" if signals[k] == 1 else "Negative",
        "Why it matters": explain(k, signals[k])
    })

st.subheader("Macro Interpretation")
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ===============================
# STOCK ENGINE (FIXED ERROR)
# ===============================
@st.cache_data(ttl=1800)
def get_stocks():

    universe = [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS",
        "INFY.NS","TCS.NS","LT.NS","ITC.NS",
        "HINDUNILVR.NS","SBIN.NS","AXISBANK.NS"
    ]

    data = []

    for s in universe:
        try:
            df = yf.download(s, period="6mo", progress=False)
            if df.empty or len(df) < 60:
                continue

            close = df["Close"]

            ret = (close.iloc[-1] / close.iloc[-60] - 1) * 100
            trend = 1 if close.iloc[-1] > close.iloc[-20] else -1

            score = ret + (trend * 5)

            data.append({
                "Stock": s,
                "Return %": round(ret, 2),
                "Score": round(score, 2)
            })

        except:
            continue

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "Return %" not in df.columns:
        return pd.DataFrame()

    df = df[df["Return %"] > 5]

    return df.sort_values("Score", ascending=False).head(10)

stocks = get_stocks()

# ===============================
# STOCK DISPLAY
# ===============================
st.subheader("Top Stock Picks")

if stocks.empty:
    st.warning("No stocks found")
else:
    st.dataframe(stocks, use_container_width=True)

# ===============================
# POSITION SIZING
# ===============================
equity_amount = portfolio_value * equity_alloc / 100

if not stocks.empty:
    per_stock = equity_amount / len(stocks)
    stocks["Allocation ₹"] = round(per_stock, 0)

    st.subheader("Position Sizing (₹ per stock)")
    st.dataframe(stocks, use_container_width=True)

# ===============================
# FOOTER
# ===============================
st.caption(f"Last Updated: {datetime.now().strftime('%d-%b %H:%M')}")
