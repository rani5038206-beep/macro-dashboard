import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# 1. MACRO SIGNALS
# =========================
signals = {
    "SPX": 1,
    "DXY": -1,
    "VIX": 1,
    "US10Y": 0
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
# 3. 🔥 YOUR SCREENER STOCKS
# =========================
# 👉 PASTE ALL 61 STOCKS HERE (VERY IMPORTANT)
SCREENER_STOCKS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "LT.NS","SBIN.NS","AXISBANK.NS","BAJFINANCE.NS","SUNPHARMA.NS"
    # 👉 ADD REST FROM SCREENER
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
        volatility = data.pct_change().std()

        df = pd.DataFrame({
            "Stock": returns_1m.index,
            "R1M": returns_1m.values,
            "R3M": returns_3m.values,
            "Vol": volatility.values
        })

        # 🔥 SMART RANKING
        df["Score"] = (df["R1M"] * 0.5) + (df["R3M"] * 0.4) - (df["Vol"] * 0.1)

        df = df.sort_values("Score", ascending=False).head(5)

        latest_prices = data.iloc[-1]

        results = []
        for _, row in df.iterrows():
            stock = row["Stock"]

            results.append({
                "name": stock.replace(".NS",""),
                "price": float(latest_prices[stock]),
                "score": float(row["Score"]),
                "r1m": float(row["R1M"] * 100),
                "r3m": float(row["R3M"] * 100)
            })

        return results

    except:
        return []

# =========================
# 5. UI HEADER
# =========================
st.title("Client Portfolio Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Market Regime", regime)
col2.metric("Model Score", model_score)
col3.metric("Recommended Equity %", model_equity)

# =========================
# 6. CLIENT INPUT
# =========================
st.sidebar.header("Client Input")

client_equity = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

# =========================
# 7. ACTION
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
# 8. PORTFOLIO IMPACT
# =========================
st.subheader("Portfolio Impact")

current_equity = portfolio_value * client_equity / 100
recommended_equity = portfolio_value * model_equity / 100

st.write(f"Current Equity: ₹{current_equity:,.0f}")
st.write(f"Recommended Equity: ₹{recommended_equity:,.0f}")

# =========================
# 9. 🔥 STOCK PICKS + POSITION SIZING
# =========================
st.subheader("🚀 Best Stocks (From Screener + Real-Time Ranking)")

stocks = get_best_stocks()

if stocks:

    total_equity = recommended_equity
    total_score = sum([abs(s["score"]) for s in stocks])

    for s in stocks:

        weight = abs(s["score"]) / total_score if total_score != 0 else 1/len(stocks)
        allocation = total_equity * weight

        price = s["price"]
        units = int(allocation / price) if price > 0 else 0
        invested = units * price

        st.markdown(f"""
### {s['name']}

• Price: ₹{price:.2f}  
• 1M Return: {s['r1m']:.2f}%  
• 3M Return: {s['r3m']:.2f}%  

👉 Allocation: ₹{allocation:,.0f}  
👉 Units to Buy: {units}  
👉 Invested Value: ₹{invested:,.0f}  

---
""")

else:
    st.warning("No stock data available")

# =========================
# 10. REFRESH BUTTON
# =========================
if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.success("Market data refreshed")
