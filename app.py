# =========================
# 1. CALCULATE MODEL FIRST
# =========================

# Example (your logic)
score = model_score  # already calculated above

if score >= 2:
    regime = "RISK ON"
    model_equity = 70

elif score <= -2:
    regime = "RISK OFF"
    model_equity = 30

else:
    regime = "TRANSITION"
    model_equity = 50


# =========================
# 2. STOCK FUNCTION
# =========================
def get_stock_details(regime):

    universe = {
        "RELIANCE.NS": "Large cap growth",
        "TCS.NS": "Stable IT leader",
        "INFY.NS": "Tech momentum",
        "HDFCBANK.NS": "Banking leader",
        "ICICIBANK.NS": "High growth bank",
        "LT.NS": "Infra growth",
        "ITC.NS": "Defensive FMCG",
        "HINDUNILVR.NS": "Stable FMCG",
        "SBIN.NS": "PSU bank momentum",
        "AXISBANK.NS": "Private bank growth"
    }

    try:
        data = yf.download(list(universe.keys()), period="3mo", progress=False)["Close"]

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
            name = stock.replace(".NS", "")
            price = round(latest_prices[stock], 2)

            if regime == "RISK ON":
                reason = "Strong momentum"
                risk = "Medium"

            elif regime == "RISK OFF":
                reason = "Defensive"
                risk = "Low"

            else:
                reason = "Balanced"
                risk = "Medium"

            results.append({
                "name": name,
                "price": price,
                "reason": reason,
                "risk": risk
            })

        return results

    except:
        return [
            {"name": "HDFC Bank", "price": "-", "reason": "Stable", "risk": "Low"},
            {"name": "Infosys", "price": "-", "reason": "Tech", "risk": "Medium"}
        ]


# =========================
# 3. CALL FUNCTION (NOW SAFE)
# =========================
stocks = get_stock_details(regime)


# =========================
# 4. DISPLAY
# =========================
st.subheader("Top Stock Picks (Actionable)")

for s in stocks:
    st.markdown(f"""
**{s['name']}**  
Price: ₹{s['price']}  
Reason: {s['reason']}  
Risk: {s['risk']}  
---
""")
