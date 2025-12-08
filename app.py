import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Thinking Investor Dashboard v2", layout="wide", initial_sidebar_state="expanded")

# --- Analysis Engine with Contextual Logic ---

def analyze_stock(stock):
    """
    Performs a deep, contextual analysis inspired by Buffett and Lynch, now with DIO.
    """
    # --- Buffett's Moat & Management Analysis ---
    buffett_analysis = {}
    
    # Moat Score Calculation
    moat_score = 0
    if stock['ROE'] > 15 and stock['ROCE'] > 15: moat_score += 1
    if stock['5Y Operating Margin'] > 15: moat_score += 1
    if stock['Debt to Equity'] < 0.5: moat_score += 1
    buffett_analysis['Moat Score'] = (moat_score / 3) * 100

    # Free Cash Flow Analysis (Contextual)
    fcf_positive = stock['Free Cash Flow'] > 0
    is_capex_heavy_sector = stock['Sector'] in ['Semiconductor', 'Data Center', 'Infra', 'Manufacturing', 'Green Energy']
    is_high_growth = stock['5Y Sales Growth'] > 25

    if fcf_positive:
        buffett_analysis['FCF Analysis'] = "✅ Positive FCF: The business is a cash-generating machine."
    elif is_capex_heavy_sector and is_high_growth:
        buffett_analysis['FCF Analysis'] = "⚠️ Negative FCF (Contextual Pass): Likely due to aggressive 'Growth Capex' in a high-investment sector. This is an investment in a future moat."
    else:
        buffett_analysis['FCF Analysis'] = "❌ Negative FCF: The business is consuming cash. Requires deep investigation."

    # Valuation
    if stock['PE Ratio'] < 25:
        buffett_analysis['Valuation'] = f"✅ Fairly Priced (P/E: {stock['PE Ratio']:.2f})."
    else:
        buffett_analysis['Valuation'] = f"⚠️ Expensive (P/E: {stock['PE Ratio']:.2f}). Price implies high future growth expectations."

    # --- Lynch's Story & Growth Analysis ---
    lynch_analysis = {}

    # Categorization
    if stock['5Y Profit Growth'] > 25 and stock['Market Cap'] < 75000:
        lynch_analysis['Category'] = "🚀 Fast Grower"
    elif stock['5Y Profit Growth'] < 15 and stock['Market Cap'] > 100000:
        lynch_analysis['Category'] = "🚢 Stalwart"
    elif stock['Sector'] in ['Chemicals', 'Metals', 'Auto', 'Manufacturing']:
        lynch_analysis['Category'] = "🔄 Cyclical"
    else:
        lynch_analysis['Category'] = "❓ Hybrid/Other"

    # PEG Ratio
    if stock['PEG Ratio'] < 1.2:
        lynch_analysis['PEG Analysis'] = f"✅ GARP (Growth at a Reasonable Price): PEG is attractive at {stock['PEG Ratio']:.2f}."
    else:
        lynch_analysis['PEG Analysis'] = f"❌ Expensive Growth: PEG is high at {stock['PEG Ratio']:.2f}."

    # Days of Inventory Outstanding (DIO) Analysis (NEW)
    if stock['Sales'] > 0 and stock['Inventory'] >= 0:
        dio = (stock['Inventory'] / stock['Sales']) * 365
        lynch_analysis['Inventory'] = f"✅ Inventory Days (DIO): {dio:.0f} days."
        # Add a simple warning for potentially high DIO, can be refined further
        if dio > 120 and stock['Sector'] not in ['Infra', 'Manufacturing']:
             lynch_analysis['Inventory'] += " (Note: DIO seems high)."
    else:
        lynch_analysis['Inventory'] = "✅ No Inventory/Sales data to analyze (e.g., Service company)."


    # --- Final Score & Radar Data ---
    radar_data = {
        'Quality': (stock['ROE'] + stock['ROCE']) / 2,
        'Growth': (stock['5Y Sales Growth'] + stock['5Y Profit Growth']) / 2,
        'Value': (1 / stock['PE Ratio']) * 100 if stock['PE Ratio'] > 0 else 0,
        'Safety': (1 - stock['Debt to Equity']) * 50 if stock['Debt to Equity'] < 1 else 0,
        'Moat': buffett_analysis['Moat Score']
    }
    
    return buffett_analysis, lynch_analysis, radar_data

# --- Main App UI ---
st.title("🧠 The Thinking Investor Dashboard v2")
st.markdown("An advanced analysis tool using contextual logic and key efficiency metrics like **Days of Inventory Outstanding (DIO)**.")

# --- File Uploader and Data Processing ---
uploaded_file = st.file_uploader("📂 Upload your Final Stock CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- Data Validation ---
        required_columns = ['Ticker', 'Sector', 'Market Cap', 'PE Ratio', 'PEG Ratio', 'Debt to Equity', 'ROE', 'ROCE', '5Y Sales Growth', '5Y Profit Growth', 'Promoter Holding', 'Free Cash Flow', '5Y Operating Margin', 'Inventory', 'Sales']
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV file is missing required columns. Please ensure it contains: {', '.join(required_columns)}")
        else:
            # --- Process Data ---
            all_results = []
            for _, row in df.iterrows():
                if not row.isnull().any():
                    b_analysis, l_analysis, r_data = analyze_stock(row)
                    all_results.append({
                        'Ticker': row['Ticker'],
                        'Buffett': b_analysis,
                        'Lynch': l_analysis,
                        'Radar': r_data
                    })
            
            # --- Portfolio Overview ---
            st.header("🚀 Portfolio Overview")
            st.markdown("A high-level look at your portfolio's characteristics.")
            
            plot_df = df.copy()
            plot_df['Moat Score'] = [res['Radar']['Moat'] for res in all_results]
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Moat vs. Valuation")
                fig_bubble = px.scatter(
                    plot_df, x='PE Ratio', y='ROE', size='Market Cap', color='Sector',
                    hover_name='Ticker', size_max=60,
                    labels={'PE Ratio': 'Valuation (P/E Ratio) →', 'ROE': 'Quality (ROE %) ↑'},
                    title="Portfolio Positioning"
                )
                fig_bubble.update_layout(xaxis_title="Lower is Cheaper", yaxis_title="Higher is Better Quality")
                st.plotly_chart(fig_bubble, use_container_width=True)

            with c2:
                st.subheader("Average Factor Exposure")
                avg_radar = {k: sum(d['Radar'][k] for d in all_results) / len(all_results) for k in all_results[0]['Radar']}
                fig_radar_avg = go.Figure()
                fig_radar_avg.add_trace(go.Scatterpolar(
                    r=list(avg_radar.values()),
                    theta=list(avg_radar.keys()),
                    fill='toself',
                    name='Portfolio Average'
                ))
                fig_radar_avg.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    title="Portfolio's Core DNA"
                )
                st.plotly_chart(fig_radar_avg, use_container_width=True)

            # --- Detailed Stock Analysis ---
            st.header("🔍 Deep-Dive Analysis")
            st.markdown("A detailed breakdown of each company in your portfolio.")

            for res in all_results:
                ticker = res['Ticker']
                with st.container():
                    st.markdown("---")
                    st.subheader(f"🏢 {ticker}")
                    
                    col1, col2 = st.columns([0.6, 0.4])
                    
                    with col1:
                        st.markdown(f"**Peter Lynch's Story:** `{res['Lynch']['Category']}`")
                        st.markdown(f"**Growth vs. Price:** {res['Lynch']['PEG Analysis']}")
                        st.markdown(f"**Inventory Efficiency:** {res['Lynch']['Inventory']}")
                        st.markdown("---")
                        st.markdown(f"**Warren Buffett's Moat:** `{res['Buffett']['Moat Score']:.0f}%` (Quality, Margins, Low Debt)")
                        st.markdown(f"**Cash Flow Status:** {res['Buffett']['FCF Analysis']}")
                        st.markdown(f"**Valuation Check:** {res['Buffett']['Valuation']}")

                    with col2:
                        fig_radar_ind = go.Figure()
                        fig_radar_ind.add_trace(go.Scatterpolar(
                            r=list(res['Radar'].values()),
                            theta=list(res['Radar'].keys()),
                            fill='toself',
                            name=ticker
                        ))
                        fig_radar_ind.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            title=f"{ticker}'s DNA",
                            height=300
                        )
                        st.plotly_chart(fig_radar_ind, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        st.exception(e)

else:
    st.info("Awaiting your Final CSV file to build the dashboard...")

