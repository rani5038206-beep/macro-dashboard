import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Client Portfolio Dashboard", layout="wide")

# =========================
# 1. GENERATE MODEL SCORE
# =========================

# Dummy signals (replace with your real macro later)
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
# 3. STOCK ENGINE (CACHED)
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

        latest_prices = data.iloc[-1]
        returns = (data.iloc[-1] / data.iloc[0] - 1).sort_values(ascending=False)

        if regime == "RISK ON":
            selected = returns.head(5)

        elif regime == "RISK OFF":
            selected = returns.tail(5)

        else:
            selected = returns.iloc[2:7]

        results = []

        for stock in selected.index:
            results.append({
                "name": stock.replace(".NS",""),
                "price": round(latest_prices[stock],2),
                "return": round(returns[stock]*100,2)
            })

        return results

    except:
        return []


stocks = get_stock_details(regime)


# =========================
# 4. UI (FINAL OUTPUT)
# =========================

st.title("Client Portfolio Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Market Regime", regime)
col2.metric("Model Score", model_score)
col3.metric("Recommended Equity %", model_equity)


# =========================
# CLIENT INPUT
# =========================

st.sidebar.header("Client Input")

client_equity = st.sidebar.slider("Equity %", 0, 100, 60)
portfolio_value = st.sidebar.number_input("Portfolio Value", value=1000000)


# =========================
# ACTION LOGIC
# =========================

diff = model_equity - client_equity

st.subheader("Action Required")

if diff > 0:
    st.success(f"Increase equity by {diff}%")

elif diff < 0:
    st.error(f"Reduce equity by {abs(diff)}%")

else:
    st.info("Portfolio aligned")


# =========================
# PORTFOLIO IMPACT
# =========================

st.subheader("Portfolio Impact")

current_equity = portfolio_value * client_equity / 100
recommended_equity = portfolio_value * model_equity / 100

st.write(f"Current Equity: ₹{current_equity:,.0f}")
st.write(f"Recommended Equity: ₹{recommended_equity:,.0f}")


# =========================
# STOCK PICKS
# =========================

st.subheader("Top Stock Picks")

if stocks:
    for s in stocks:
        st.markdown(f"""
**{s['name']}**  
Price: ₹{s['price']}  
3M Return: {s['return']}%  
---
""")
else:
    st.warning("Stock data unavailable")
