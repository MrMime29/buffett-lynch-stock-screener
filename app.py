import streamlit as st
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Investor Checklist", layout="centered")

# --- Helper Functions for Analysis ---

def check_buffett(stock):
    """Analyzes a stock based on Warren Buffett's core principles."""
    results = []
    # 1. Consistent Profitability (ROE > 15%)
    if stock['ROE'] > 15:
        results.append("✅ **Consistent Profitability:** ROE is above 15%, indicating an efficient business.")
    else:
        results.append(f"❌ **Inconsistent Profitability:** ROE is {stock['ROE']:.2f}%, below the 15% threshold.")

    # 2. Low Debt (Debt to Equity < 0.5)
    if stock['Debt to Equity'] < 0.5:
        results.append("✅ **Low Debt:** Debt to Equity is low, suggesting a strong balance sheet.")
    else:
        results.append(f"❌ **High Debt:** Debt to Equity is {stock['Debt to Equity']:.2f}, which is higher than ideal.")

    # 3. Fair Valuation (P/E Ratio < 25)
    if stock['PE Ratio'] < 25:
        results.append("✅ **Fair Valuation:** P/E Ratio is reasonable, not excessively expensive.")
    else:
        results.append(f"❌ **Potentially Overvalued:** P/E Ratio is {stock['PE Ratio']:.2f}, suggesting high market expectations.")
        
    return results

def check_lynch(stock):
    """Analyzes a stock based on Peter Lynch's growth and value principles."""
    results = []
    # 1. Strong Earnings Growth (Profit Growth > 20%)
    if stock['5Y Profit Growth'] > 20:
        results.append("✅ **Strong Earnings Growth:** 5-year profit growth is impressive.")
    else:
        results.append(f"❌ **Slow Earnings Growth:** 5-year profit growth is {stock['5Y Profit Growth']:.2f}%, below the 20% target.")

    # 2. Reasonable Valuation (PEG Ratio < 1.2)
    if stock['PEG Ratio'] < 1.2:
        results.append("✅ **Growth at a Reasonable Price (GARP):** PEG ratio is attractive.")
    else:
        results.append(f"❌ **Expensive Growth:** PEG ratio is {stock['PEG Ratio']:.2f}, suggesting the price may have run ahead of growth.")

    # 3. Low Promoter Pledging (Pledged % < 5%)
    if stock['Promoter Holding Pledged'] < 5:
        results.append("✅ **Low Promoter Pledging:** Indicates confidence from the management.")
    else:
        results.append(f"❌ **High Promoter Pledging:** Pledged holding is {stock['Promoter Holding Pledged']:.2f}%, a potential red flag.")
        
    return results

# --- Main App UI ---
st.title("Investor Checklist: Buffett vs. Lynch")
st.markdown("Upload your stock data to see how it stacks up against the masters.")

uploaded_file = st.file_uploader("📂 Upload your Stock CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- Data Validation ---
        required_columns = ['Ticker', 'ROE', 'Debt to Equity', 'PE Ratio', '5Y Profit Growth', 'PEG Ratio', 'Promoter Holding Pledged']
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV file is missing required columns. Please ensure it contains: {', '.join(required_columns)}")
        else:
            # =================================================================
            # THE FIX: Data Cleaning & Conversion Section
            # =================================================================
            st.info("Cleaning and converting data types...")
            numeric_cols = ['ROE', 'Debt to Equity', 'PE Ratio', '5Y Profit Growth', 'PEG Ratio', 'Promoter Holding Pledged']
            
            for col in numeric_cols:
                # pd.to_numeric will convert columns to numbers. 
                # The 'coerce' argument turns any problematic values (like text) into NaN (Not a Number)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop any rows that have missing values after conversion
            df.dropna(inplace=True)
            # =================================================================
            # End of Fix
            # =================================================================

            if df.empty:
                st.error("Analysis could not be performed. All rows in the CSV file contained invalid or missing data after cleaning. Please check your CSV file.")
            else:
                for index, row in df.iterrows():
                    st.markdown("---")
                    st.header(f"Analysis for: {row['Ticker']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Buffett Checklist")
                        buffett_results = check_buffett(row)
                        for result in buffett_results:
                            st.markdown(result)
                            
                    with col2:
                        st.subheader("Lynch Checklist")
                        lynch_results = check_lynch(row)
                        for result in lynch_results:
                            st.markdown(result)

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
        st.exception(e) # This will show the full error traceback for debugging

else:
    st.info("Awaiting your CSV file to begin analysis...")

