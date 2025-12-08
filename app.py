import streamlit as st
import pandas as pd

# --- Helper Functions for Analysis ---

def analyze_buffett(stock):
    """
    Analyzes a stock based on Warren Buffett's principles.
    Returns a list of strings explaining the results.
    """
    results = []
    score = 0
    total_criteria = 5

    # 1. Understandable Business (Qualitative - we use Market Cap as a proxy for established business)
    if stock['Market Cap'] > 10000:
        results.append("✅ **Large, Established Business:** Market Cap is over ₹10,000 Cr, suggesting a significant and likely understandable business.")
        score += 1
    else:
        results.append("❌ **Smaller Business:** Market Cap is below ₹10,000 Cr. Requires deeper investigation to ensure it's a durable business.")

    # 2. Low Debt (Durable Competitive Advantage)
    if stock['Debt to Equity'] < 0.5:
        results.append(f"✅ **Low Debt:** Debt to Equity ratio is {stock['Debt to Equity']:.2f}, which is below the 0.5 threshold. The company is not overly burdened by debt.")
        score += 1
    else:
        results.append(f"❌ **High Debt:** Debt to Equity ratio is {stock['Debt to Equity']:.2f}. Buffett prefers companies that don't rely on heavy borrowing.")

    # 3. High Return on Equity (ROE) & ROCE (Profitability)
    if stock['ROE'] > 15 and stock['ROCE'] > 15:
        results.append(f"✅ **High Profitability:** ROE ({stock['ROE']:.2f}%) and ROCE ({stock['ROCE']:.2f}%) are both above 15%, indicating efficient use of capital and equity.")
        score += 1
    else:
        results.append(f"❌ **Mediocre Profitability:** ROE ({stock['ROE']:.2f}%) or ROCE ({stock['ROCE']:.2f}%) is below 15%. The company may not be as profitable as a Buffett-style investment.")

    # 4. Competent Management (Proxy: Promoter Holding)
    if stock['Promoter Holding'] > 40:
        results.append(f"✅ **Significant Promoter Holding:** Promoters hold {stock['Promoter Holding']:.2f}%, showing they have significant skin in the game.")
        score += 1
    else:
        results.append(f"❌ **Low Promoter Holding:** Promoters hold {stock['Promoter Holding']:.2f}%. Requires checking if the company is institutionally managed.")

    # 5. Sensible Valuation (Proxy: P/E Ratio)
    if stock['PE Ratio'] < 25:
        results.append(f"✅ **Reasonable Valuation:** P/E Ratio is {stock['PE Ratio']:.2f}, which is below 25. Buffett seeks wonderful companies at a fair price.")
        score += 1
    else:
        results.append(f"❌ **Expensive Valuation:** P/E Ratio is {stock['PE Ratio']:.2f}. The stock may be overvalued, requiring strong justification for its high price.")
        
    return results, score, total_criteria

def analyze_lynch(stock):
    """
    Analyzes a stock based on Peter Lynch's principles.
    Returns a list of strings explaining the results.
    """
    results = []
    score = 0
    total_criteria = 4

    # 1. Favorable PEG Ratio (Price vs. Growth)
    # Lynch's most famous metric. A PEG below 1 is considered very good.
    if stock['PEG Ratio'] < 1.0:
        results.append(f"✅ **Excellent PEG Ratio:** PEG Ratio is {stock['PEG Ratio']:.2f}. The stock's price appears cheap relative to its earnings growth.")
        score += 1
    elif stock['PEG Ratio'] < 1.5:
        results.append(f"✅ **Fair PEG Ratio:** PEG Ratio is {stock['PEG Ratio']:.2f}. The stock is reasonably priced relative to its growth.")
        score += 1
    else:
        results.append(f"❌ **High PEG Ratio:** PEG Ratio is {stock['PEG Ratio']:.2f}. The stock may be expensive for its growth rate.")

    # 2. Strong Earnings Growth (Looking for "Fast Growers")
    if stock['5Y Profit Growth'] > 20:
        results.append(f"✅ **Strong Profit Growth:** 5-Year Profit Growth is {stock['5Y Profit Growth']:.2f}%, indicating a fast-growing company.")
        score += 1
    else:
        results.append(f"❌ **Slow Profit Growth:** 5-Year Profit Growth is {stock['5Y Profit Growth']:.2f}%. This may be a 'slow grower' or 'stalwart' rather than a 'fast grower'.")

    # 3. Low Debt
    if stock['Debt to Equity'] < 0.8:
        results.append(f"✅ **Manageable Debt:** Debt to Equity ratio is {stock['Debt to Equity']:.2f}. A strong balance sheet is crucial.")
        score += 1
    else:
        results.append(f"❌ **High Debt:** Debt to Equity ratio is {stock['Debt to Equity']:.2f}. Lynch was wary of excessive debt, which increases risk.")

    # 4. Is it a "Tenbagger"? (Proxy: Market Cap - smaller companies have more room to grow)
    if stock['Market Cap'] < 50000:
        results.append("✅ **Potential for High Growth:** Market Cap is below ₹50,000 Cr. The company is small enough to have explosive growth potential (a potential 'tenbagger').")
        score += 1
    else:
        results.append("❌ **Large Cap ('Stalwart'):** Market Cap is over ₹50,000 Cr. This is likely a 'stalwart' that will provide good, but not explosive, returns.")

    return results, score, total_criteria

# --- Streamlit App Layout ---

st.set_page_config(page_title="Investor Checklist Analyzer", layout="wide")

st.title("📈 Investor Checklist: Buffett vs. Lynch")
st.markdown("""
This tool analyzes stocks from your CSV file based on the fundamental principles of **Warren Buffett** (looking for wonderful companies at a fair price) and **Peter Lynch** (looking for growth at a reasonable price).

**Instructions:**
1.  Prepare a CSV file with the required columns: `Ticker`, `Market Cap`, `PE Ratio`, `PEG Ratio`, `Debt to Equity`, `ROE`, `ROCE`, `5Y Sales Growth`, `5Y Profit Growth`, `Promoter Holding`.
2.  Upload your file using the button below.
3.  The analysis for each stock will appear automatically.
""")

uploaded_file = st.file_uploader("📂 Upload your Stock CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully! Here is the analysis:")

        # Check if required columns exist
        required_columns = ['Ticker', 'Market Cap', 'PE Ratio', 'PEG Ratio', 'Debt to Equity', 'ROE', 'ROCE', '5Y Sales Growth', '5Y Profit Growth', 'Promoter Holding']
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV file is missing one or more required columns. Please ensure it contains: {', '.join(required_columns)}")
        else:
            for index, row in df.iterrows():
                # Handle potential missing data in a row
                if row.isnull().any():
                    st.warning(f"Skipping analysis for **{row['Ticker']}** due to missing data in the row.")
                    continue

                st.markdown("---")
                st.header(f"Analysis for: {row['Ticker']}")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(" Buffett Checklist")
                    buffett_results, buffett_score, buffett_total = analyze_buffett(row)
                    st.progress(buffett_score / buffett_total)
                    st.metric(label="Buffett Score", value=f"{buffett_score}/{buffett_total}")
                    for result in buffett_results:
                        st.markdown(result)

                with col2:
                    st.subheader(" Lynch Checklist")
                    lynch_results, lynch_score, lynch_total = analyze_lynch(row)
                    st.progress(lynch_score / lynch_total)
                    st.metric(label="Lynch Score", value=f"{lynch_score}/{lynch_total}")
                    for result in lynch_results:
                        st.markdown(result)

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

else:
    st.info("Awaiting CSV file upload...")

