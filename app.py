import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def compute_basic_metrics(ticker: str):
    """
    Fetch metrics using yfinance.
    This version is cached and handles rate limits + generic errors.
    """
    metrics = {
        "error": None,
        "revenue_cagr_3y": None,
        "eps_growth_3y": None,
        "roe": None,
        "debt_to_equity": None,
        "free_cash_flow": None,
        "pe": None,
        "peg": None,
        "dividend_yield": None,
        "profit_margin": None,
    }

    try:
        t = yf.Ticker(ticker)

        # This call is often what triggers rate limits
        try:
            info = t.info
        except YFRateLimitError as e:
            metrics["error"] = "rate_limit"
            return metrics
        except Exception:
            info = {}

        financials = t.financials
        balance_sheet = t.balance_sheet
        cashflow = t.cashflow
        earnings = t.earnings

        metrics["pe"] = info.get("trailingPE")
        metrics["peg"] = info.get("pegRatio")
        metrics["dividend_yield"] = info.get("dividendYield")
        metrics["profit_margin"] = info.get("profitMargins")

        # ---- Revenue CAGR ----
        try:
            if earnings is not None and not earnings.empty:
                rev = earnings["Revenue"].sort_index()
                if len(rev) >= 3:
                    rev_first = rev.iloc[-3]
                    rev_last = rev.iloc[-1]
                    if rev_first > 0 and rev_last > 0:
                        years = 2
                        metrics["revenue_cagr_3y"] = (rev_last / rev_first) ** (1/years) - 1
        except Exception:
            pass

        # ---- EPS growth ----
        try:
            if earnings is not None and not earnings.empty:
                e = earnings["Earnings"].sort_index()
                if len(e) >= 3:
                    e_first = e.iloc[-3]
                    e_last = e.iloc[-1]
                    if e_first != 0:
                        metrics["eps_growth_3y"] = (e_last / e_first) ** (1/2) - 1
        except Exception:
            pass

        # ---- ROE ----
        try:
            if financials is not None and not financials.empty and balance_sheet is not None and not balance_sheet.empty:
                ni = financials.loc["Net Income"].iloc[0]
                total_equity = balance_sheet.loc["Total Stockholder Equity"].iloc[0]
                if total_equity:
                    metrics["roe"] = ni / total_equity
        except Exception:
            pass

        # ---- Debt to equity ----
        try:
            if balance_sheet is not None and not balance_sheet.empty:
                total_debt = balance_sheet.loc["Total Debt"].iloc[0] if "Total Debt" in balance_sheet.index else None
                total_equity = balance_sheet.loc["Total Stockholder Equity"].iloc[0]
                if total_equity and total_debt is not None:
                    metrics["debt_to_equity"] = total_debt / total_equity
        except Exception:
            pass

        # ---- Free cash flow ----
        try:
            if cashflow is not None and not cashflow.empty:
                ocf = cashflow.loc["Total Cash From Operating Activities"].iloc[0]
                capex = cashflow.loc["Capital Expenditures"].iloc[0]
                metrics["free_cash_flow"] = ocf + capex
        except Exception:
            pass

        # ---- Fallback PEG calc ----
        if metrics["peg"] is None and metrics["pe"] and metrics["eps_growth_3y"]:
            g_pct = metrics["eps_growth_3y"] * 100
            if g_pct > 0:
                metrics["peg"] = metrics["pe"] / g_pct

    except YFRateLimitError:
        metrics["error"] = "rate_limit"
    except Exception as e:
        metrics["error"] = str(e)

    return metrics
