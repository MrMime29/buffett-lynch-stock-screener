import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# -----------------------------
# Helper functions to get metrics
# -----------------------------

def safe_div(a, b):
    try:
        if b == 0 or b is None or a is None:
            return None
        return a / b
    except Exception:
        return None

def compute_basic_metrics(ticker: str):
    """
    Fetch metrics using yfinance and compute:
    - revenue CAGR
    - EPS growth
    - ROE
    - debt to equity
    - free cash flow
    - PE
    - PEG (rough)
    """
    t = yf.Ticker(ticker)

    info = t.info if hasattr(t, "info") else {}
    financials = t.financials
    balance_sheet = t.balance_sheet
    cashflow = t.cashflow
    earnings = t.earnings  # yearly

    metrics = {
        "revenue_cagr_3y": None,
        "eps_growth_3y": None,
        "roe": None,
        "debt_to_equity": None,
        "free_cash_flow": None,
        "pe": info.get("trailingPE"),
        "peg": info.get("pegRatio"),
        "dividend_yield": info.get("dividendYield"),
        "profit_margin": info.get("profitMargins"),
    }

    # ---- Revenue CAGR (3y) ----
    try:
        if earnings is not None and not earnings.empty:
            # earnings index is years, columns: Revenue, Earnings
            rev = earnings["Revenue"].sort_index()
            if len(rev) >= 3:
                rev_first = rev.iloc[-3]
                rev_last = rev.iloc[-1]
                if rev_first > 0 and rev_last > 0:
                    years = 2  # last 3 points = 2 intervals
                    metrics["revenue_cagr_3y"] = (rev_last / rev_first) ** (1 / years) - 1
    except Exception:
        pass

    # ---- EPS growth (use Earnings column as proxy) ----
    try:
        if earnings is not None and not earnings.empty:
            e = earnings["Earnings"].sort_index()
            if len(e) >= 3:
                e_first = e.iloc[-3]
                e_last = e.iloc[-1]
                if e_first != 0:
                    metrics["eps_growth_3y"] = (e_last / e_first) ** (1 / 2) - 1
    except Exception:
        pass

    # ---- ROE (Net income / Equity) ----
    try:
        if financials is not None and not financials.empty and balance_sheet is not None and not balance_sheet.empty:
            # Use last column (most recent year)
            ni = financials.loc["Net Income"].iloc[0]
            total_equity = balance_sheet.loc["Total Stockholder Equity"].iloc[0]
            metrics["roe"] = safe_div(ni, total_equity)
    except Exception:
        pass

    # ---- Debt to equity ----
    try:
        if balance_sheet is not None and not balance_sheet.empty:
            total_debt = balance_sheet.loc["Total Debt"].iloc[0] if "Total Debt" in balance_sheet.index else None
            total_equity = balance_sheet.loc["Total Stockholder Equity"].iloc[0]
            metrics["debt_to_equity"] = safe_div(total_debt, total_equity)
    except Exception:
        pass

    # ---- Free cash flow (most recent) ----
    try:
        if cashflow is not None and not cashflow.empty:
            # Free cash flow approx = Operating CF - Capex
            ocf = cashflow.loc["Total Cash From Operating Activities"].iloc[0]
            capex = cashflow.loc["Capital Expenditures"].iloc[0]
            metrics["free_cash_flow"] = ocf + capex  # capex usually negative
    except Exception:
        pass

    # If PEG missing, try compute from PE and growth
    if metrics["peg"] is None and metrics["pe"] and metrics["eps_growth_3y"]:
        g_pct = metrics["eps_growth_3y"] * 100
        if g_pct > 0:
            metrics["peg"] = metrics["pe"] / g_pct

    return metrics


# -----------------------------
# Buffett-style scoring
# -----------------------------

def buffett_score(metrics: dict) -> (float, dict):
    """
    Quantitative Buffett-style score (0–10) based on:
    ROE, debt, revenue growth, profit margin, FCF, PE, dividend.
    """
    detail = {}
    score = 0.0

    # 1. ROE > 15%
    roe = metrics.get("roe")
    if roe is not None:
        if roe > 0.15:
            score += 1
            detail["ROE"] = "Good (>15%)"
        elif roe > 0.10:
            score += 0.5
            detail["ROE"] = "Average (10–15%)"
        else:
            detail["ROE"] = "Weak"
    else:
        detail["ROE"] = "No data"

    # 2. Revenue CAGR 3y
    rev_cagr = metrics.get("revenue_cagr_3y")
    if rev_cagr is not None:
        if rev_cagr > 0.10:
            score += 1
            detail["Revenue Growth"] = "Strong (>10% CAGR)"
        elif rev_cagr > 0:
            score += 0.5
            detail["Revenue Growth"] = "Positive but modest"
        else:
            detail["Revenue Growth"] = "Flat/negative"
    else:
        detail["Revenue Growth"] = "No data"

    # 3. Profit margin
    pm = metrics.get("profit_margin")
    if pm is not None:
        if pm > 0.15:
            score += 1
            detail["Profit Margin"] = "High (>15%)"
        elif pm > 0.05:
            score += 0.5
            detail["Profit Margin"] = "Moderate (5–15%)"
        else:
            detail["Profit Margin"] = "Low"
    else:
        detail["Profit Margin"] = "No data"

    # 4. Debt to equity
    de = metrics.get("debt_to_equity")
    if de is not None:
        if de < 0.5:
            score += 1
            detail["Debt"] = "Low (D/E < 0.5)"
        elif de < 1:
            score += 0.5
            detail["Debt"] = "Moderate (0.5–1)"
        else:
            detail["Debt"] = "High"
    else:
        detail["Debt"] = "No data"

    # 5. Free cash flow
    fcf = metrics.get("free_cash_flow")
    if fcf is not None:
        if fcf > 0:
            score += 1
            detail["Free Cash Flow"] = "Positive"
        else:
            detail["Free Cash Flow"] = "Negative"
    else:
        detail["Free Cash Flow"] = "No data"

    # 6. PE (reasonable valuation)
    pe = metrics.get("pe")
    if pe is not None:
        if 5 < pe < 25:
            score += 1
            detail["PE"] = "Reasonable (5–25)"
        elif 0 < pe < 35:
            score += 0.5
            detail["PE"] = "Acceptable (<35)"
        else:
            detail["PE"] = "Possibly expensive"
    else:
        detail["PE"] = "No data"

    # 7. Dividend yield (bonus point)
    dy = metrics.get("dividend_yield")
    if dy is not None and dy > 0:
        if dy > 0.02:
            score += 1
            detail["Dividend"] = "Good yield (>2%)"
        else:
            score += 0.5
            detail["Dividend"] = "Low but positive"
    else:
        detail["Dividend"] = "No/unknown"

    # Normalize to max 10 (our max is 7 so far, scale up)
    max_raw = 7.0
    norm_score = round((score / max_raw) * 10, 2)
    return norm_score, detail


# -----------------------------
# Peter Lynch-style scoring
# -----------------------------

def lynch_score(metrics: dict) -> (float, dict):
    """
    Peter Lynch-style quantitative score (0–10) around:
    growth, PEG, debt, cash flow.
    """
    detail = {}
    score = 0.0

    # 1. EPS growth 10–25%
    eps_g = metrics.get("eps_growth_3y")
    if eps_g is not None:
        g_pct = eps_g * 100
        if 10 <= g_pct <= 25:
            score += 2
            detail["EPS Growth"] = "Ideal (10–25% p.a.)"
        elif 5 <= g_pct < 10 or 25 < g_pct <= 35:
            score += 1
            detail["EPS Growth"] = "Acceptable"
        elif g_pct > 0:
            score += 0.5
            detail["EPS Growth"] = "Low but positive"
        else:
            detail["EPS Growth"] = "Weak/negative"
    else:
        detail["EPS Growth"] = "No data"

    # 2. PEG < 1
    peg = metrics.get("peg")
    if peg is not None:
        if peg < 1:
            score += 2
            detail["PEG"] = "Good (<1)"
        elif peg < 1.5:
            score += 1
            detail["PEG"] = "Okay (1–1.5)"
        else:
            detail["PEG"] = "High (>1.5)"
    else:
        detail["PEG"] = "No data"

    # 3. Debt (same as Buffett but smaller weight)
    de = metrics.get("debt_to_equity")
    if de is not None:
        if de < 0.5:
            score += 1
            detail["Debt"] = "Low"
        elif de < 1:
            score += 0.5
            detail["Debt"] = "Moderate"
        else:
            detail["Debt"] = "High"
    else:
        detail["Debt"] = "No data"

    # 4. Free cash flow
    fcf = metrics.get("free_cash_flow")
    if fcf is not None:
        if fcf > 0:
            score += 1
            detail["FCF"] = "Positive"
        else:
            detail["FCF"] = "Negative"
    else:
        detail["FCF"] = "No data"

    # 5. Revenue growth (supporting factor)
    rev_cagr = metrics.get("revenue_cagr_3y")
    if rev_cagr is not None:
        if rev_cagr > 0.10:
            score += 1
            detail["Revenue Growth"] = "Strong"
        elif rev_cagr > 0:
            score += 0.5
            detail["Revenue Growth"] = "Positive"
        else:
            detail["Revenue Growth"] = "Weak/negative"
    else:
        detail["Revenue Growth"] = "No data"

    # Max raw = 7; normalize to 10
    max_raw = 7.0
    norm_score = round((score / max_raw) * 10, 2)
    return norm_score, detail


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Buffett & Lynch Stock Screener", layout="wide")

st.title("📈 Buffett & Peter Lynch Stock Evaluation Tool")
st.write(
    "Upload your stock portfolio and this app will compute **quantitative** "
    "Buffett-style and Peter Lynch–style scores for each stock using Yahoo Finance data."
)

uploaded_file = st.file_uploader("Upload portfolio CSV or Excel", type=["csv", "xlsx"])

example = """
Example CSV format:
symbol,buy_price,quantity
RELIANCE.NS,2500,10
HDFCBANK.NS,1450,20
TCS.NS,3500,5
"""
with st.expander("📄 View example file format"):
    st.code(example, language="text")

if uploaded_file is not None:
    # Load data
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    required_cols = {"symbol", "buy_price"}
    if not required_cols.issubset(set(c.lower() for c in df.columns)):
        st.error("File must contain at least 'symbol' and 'buy_price' columns.")
        st.stop()

    # Normalize column names
    df.columns = [c.lower() for c in df.columns]

    st.success("File uploaded successfully. Fetching data and computing scores...")

    results = []

    for _, row in df.iterrows():
        symbol = str(row["symbol"]).strip()
        buy_price = row.get("buy_price", np.nan)
        quantity = row.get("quantity", np.nan)

        st.write(f"🔍 Processing: **{symbol}**")

        metrics = compute_basic_metrics(symbol)
        b_score, b_detail = buffett_score(metrics)
        l_score, l_detail = lynch_score(metrics)

        result_row = {
            "symbol": symbol,
            "buy_price": buy_price,
            "quantity": quantity,
            "buffett_score_0_10": b_score,
            "lynch_score_0_10": l_score,
            "revenue_cagr_3y": metrics.get("revenue_cagr_3y"),
            "eps_growth_3y": metrics.get("eps_growth_3y"),
            "roe": metrics.get("roe"),
            "debt_to_equity": metrics.get("debt_to_equity"),
            "free_cash_flow": metrics.get("free_cash_flow"),
            "pe": metrics.get("pe"),
            "peg": metrics.get("peg"),
            "dividend_yield": metrics.get("dividend_yield"),
            "profit_margin": metrics.get("profit_margin"),
        }
        results.append(result_row)

    res_df = pd.DataFrame(results)

    # Decision helper
    def decision(score_b, score_l):
        avg = (score_b + score_l) / 2
        if avg >= 8:
            return "✅ Strong – Hold / Add"
        elif avg >= 6:
            return "👍 OK – Hold / Watch"
        elif avg >= 4:
            return "⚠️ Weak – Review / Caution"
        else:
            return "❌ Poor – Avoid / Exit"

    res_df["decision"] = res_df.apply(
        lambda r: decision(r["buffett_score_0_10"], r["lynch_score_0_10"]), axis=1
    )

    st.subheader("📊 Results")
    st.dataframe(res_df)

    # Downloadable results
    csv = res_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download results as CSV",
        data=csv,
        file_name="buffett_lynch_scored_portfolio.csv",
        mime="text/csv",
    )

else:
    st.info("Upload a CSV or Excel file to begin.")
