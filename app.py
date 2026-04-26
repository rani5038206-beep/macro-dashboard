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
# 2. REGIME LOGIC
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
# 3. STOCK ENGINE
# =========================
@st.cache_data(ttl=3600)
def get_stock_details(regime):

    universe = [
        "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS",
        "ICICIBANK.NS","LT.NS","ITC.NS","HINDUNILVR.NS",
        "SBIN.NS","AXISBANK.NS"
    ]

    try:
        data = yf.download(universe, period="3mo", progress=False)["Close"]

        latest = data.iloc[-1]
        returns = (data.iloc[-1] / data.iloc[0] - 1).sort_values(ascending=False)

        if regime == "RISK ON":
            selected = returns.head(5)

        elif regime == "RISK OFF":
            selected = returns.tail(5)

        else:
            selected = returns.iloc[2:7]

        result = []
        for stock in selected.index:
            result.append({
                "name": stock.replace(".NS",""),
                "price": float(latest[stock]),
                "return": float(returns[stock] * 100)
            })

        return result

    except:
        return []

stocks = get_stock_details(regime)

# =========================
# 4. UI HEADER
# =========================
st.title("Client Portfolio Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Market Regime", regime)
col2.metric("Model Score", model_score)
col3.metric("Recommended Equity %", model_equity)

# =========================
# 5. CLIENT INPUT
# =========================
st.sidebar.header("Client Input")

client_equity = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1000000)

# =========================
# 6. ACTION REQUIRED
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
# 7. PORTFOLIO IMPACT
# =========================
st.subheader("Portfolio Impact")

current_equity = portfolio_value * client_equity / 100
recommended_equity = portfolio_value * model_equity / 100

st.write(f"Current Equity: ₹{current_equity:,.0f}")
st.write(f"Recommended Equity: ₹{recommended_equity:,.0f}")

# =========================
# 8. POSITION SIZING ENGINE
# =========================
st.subheader("Top Stock Picks (With Allocation & Units)")

if stocks:

    total_equity_amount = recommended_equity

    # 🔥 Momentum-based allocation
    total_return_weight = sum([abs(s["return"]) for s in stocks])

    for s in stocks:

        weight = abs(s["return"]) / total_return_weight if total_return_weight != 0 else 1/len(stocks)
        allocation = total_equity_amount * weight

        price = s["price"]

        if price > 0:
            units = int(allocation / price)
        else:
            units = 0

        invested_value = units * price

        st.markdown(f"""
### {s['name']}

• Price: ₹{price:.2f}  
• 3M Return: {s['return']:.2f}%  

👉 Allocation: ₹{allocation:,.0f}  
👉 Units to Buy: {units}  
👉 Invested Value: ₹{invested_value:,.0f}  

---
""")

else:
    st.warning("Stock data unavailable")
