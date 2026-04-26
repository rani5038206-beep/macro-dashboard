import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# 1. MACRO DATA (REAL)
# =========================
@st.cache_data(ttl=600)
def get_macro_data():
    try:
        df = yf.download(
            ["^GSPC","DX-Y.NYB","^VIX","^TNX"],
            period="6mo",
            progress=False
        )["Close"].dropna()

        df.columns = ["SPX","DXY","VIX","US10Y"]
        return df
    except:
        return pd.DataFrame()

df_macro = get_macro_data()

if df_macro.empty:
    st.error("Market data not available")
    st.stop()

latest = df_macro.iloc[-1]
prev = df_macro.iloc[-2]

signals = {
    "SPX": 1 if latest["SPX"] > prev["SPX"] else -1,
    "DXY": -1 if latest["DXY"] > prev["DXY"] else 1,
    "VIX": -1 if latest["VIX"] > prev["VIX"] else 1,
    "US10Y": -1 if latest["US10Y"] > prev["US10Y"] else 1
}

model_score = sum(signals.values())

# =========================
# 2. REGIME
# =========================
if model_score >= 2:
    regime = "RISK ON"
    model_equity = 70
elif model_score <= -2:
    regime = "RISK OFF"
    model_equity = 30
else:
    regime = "TRANSITION"
    model_equity = 50

# =========================
# 3. YOUR SCREENER STOCKS
# =========================
SCREENER_STOCKS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "LT.NS","SBIN.NS","AXISBANK.NS","BAJFINANCE.NS","SUNPHARMA.NS"
]

# =========================
# 4. STOCK ENGINE
# =========================
@st.cache_data(ttl=300)
def get_best_stocks():

    try:
        data = yf.download(SCREENER_STOCKS, period="3mo", progress=False)["Close"]

        returns_1m = (data.iloc[-1] / data.iloc[-20] - 1)
        returns_3m = (data.iloc[-1] / data.iloc[0] - 1)
        vol = data.pct_change().std()

        df = pd.DataFrame({
            "Stock": returns_1m.index,
            "R1M": returns_1m.values,
            "R3M": returns_3m.values,
            "Vol": vol.values
        })

        df["Score"] = (df["R1M"]*0.5) + (df["R3M"]*0.4) - (df["Vol"]*0.1)

        df = df.sort_values("Score", ascending=False).head(5)

        latest_prices = data.iloc[-1]

        result = []
        for _, row in df.iterrows():
            s = row["Stock"]
            result.append({
                "name": s.replace(".NS",""),
                "price": float(latest_prices[s]),
                "score": float(row["Score"]),
                "r1m": float(row["R1M"]*100),
                "r3m": float(row["R3M"]*100)
            })

        return result

    except:
        return []

# =========================
# 5. UI HEADER
# =========================
st.title("Client Portfolio Dashboard")

c1,c2,c3 = st.columns(3)
c1.metric("Market Regime", regime)
c2.metric("Model Score", model_score)
c3.metric("Equity Allocation", f"{model_equity}%")

# =========================
# 6. MACRO SIGNAL DISPLAY
# =========================
st.subheader("Macro Signals")

st.table(pd.DataFrame(signals, index=["Signal"]).T)

st.subheader("Market Trend")
st.line_chart(df_macro)

# =========================
# 7. CLIENT INPUT
# =========================
st.sidebar.header("Client Input")

client_equity = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

# =========================
# 8. ACTION
# =========================
st.subheader("Action Required")

diff = model_equity - client_equity

if diff > 0:
    st.success(f"Increase equity by {diff}%")
elif diff < 0:
    st.error(f"Reduce equity by {abs(diff)}%")
else:
    st.info("Portfolio aligned")

# =========================
# 9. STOCK PICKS + ALLOCATION
# =========================
st.subheader("Top Stocks (Screener + Real-Time)")

stocks = get_best_stocks()

recommended_equity = portfolio_value * model_equity / 100

if stocks:

    total_score = sum([abs(s["score"]) for s in stocks])

    for s in stocks:

        weight = abs(s["score"]) / total_score if total_score != 0 else 1/len(stocks)
        allocation = recommended_equity * weight

        price = s["price"]
        units = int(allocation / price) if price > 0 else 0

        st.markdown(f"""
### {s['name']}

• Price: ₹{price:.2f}  
• 1M Return: {s['r1m']:.2f}%  
• 3M Return: {s['r3m']:.2f}%  

👉 Allocation: ₹{allocation:,.0f}  
👉 Units: {units}

---
""")

else:
    st.warning("No stock data")

# =========================
# 10. REFRESH
# =========================
if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.success("Updated")
