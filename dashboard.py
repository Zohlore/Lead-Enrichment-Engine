import streamlit as st
import pandas as pd
import time
from enricher import enricher
from email_generator import email_generator
from cache import cache
from logger import logger

st.set_page_config(
    page_title="Lead Enrichment Engine",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 B2B Lead Enrichment Engine")
st.markdown("""
Automatically enrich company data and generate personalized outreach emails.
*Cost-optimized with SQLite caching to reduce API calls.*
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Cache stats
    st.subheader("💾 Cache Status")
    stats = cache.get_cache_stats()
    col1, col2 = st.columns(2)
    col1.metric("Cached Companies", stats['total_cached'])
    col2.metric("Fresh", stats['fresh_cached'])
    
    st.progress(stats['fresh_cached'] / max(stats['total_cached'], 1))
    st.caption(f"TTL: {stats['ttl_hours']} hours")
    
    if st.button("🗑️ Clear Stale Cache"):
        cache.clear_stale()
        st.rerun()
    
    st.markdown("---")
    st.caption("Built with LangGraph, OpenAI, SQLite, Streamlit")

# Main content
tab1, tab2, tab3 = st.tabs(["📥 Enrich Companies", "📧 Generate Emails", "📊 Analytics"])

with tab1:
    st.subheader("Enrich Company Data")
    
    # Input method
    input_method = st.radio("Choose input method:", ["Single Company", "CSV Upload"])
    
    if input_method == "Single Company":
        company_name = st.text_input("Company Name", placeholder="e.g., Acme Corp")
        generate_email_check = st.checkbox("Also generate outreach email")
        
        if st.button("🔍 Enrich", type="primary"):
            if company_name:
                with st.spinner(f"Enriching {company_name}..."):
                    result = enricher.enrich_company(company_name)
                    
                    if result.from_cache:
                        st.info("📦 Data retrieved from cache (cost saved!)")
                    
                    st.success(f"✅ Enriched {company_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Processing Time", f"{result.processing_time_ms:.0f}ms")
                    with col2:
                        st.metric("Cost", f"${result.cost_estimate_usd:.4f}")
                    
                    # Display company data
                    company = result.company
                    st.subheader(f"📊 {company.company_name}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption("Industry")
                        st.write(company.industry or "N/A")
                    with col2:
                        st.caption("Employees")
                        st.write(company.employee_count or "N/A")
                    with col3:
                        st.caption("Founded")
                        st.write(company.founded_year or "N/A")
                    
                    if company.ceo:
                        st.caption("Leadership")
                        leadership = []
                        if company.ceo: leadership.append(f"CEO: {company.ceo}")
                        if company.cto: leadership.append(f"CTO: {company.cto}")
                        if company.head_of_sales: leadership.append(f"Head of Sales: {company.head_of_sales}")
                        st.write(", ".join(leadership) if leadership else "N/A")
                    
                    if company.recent_news:
                        st.caption("Recent News")
                        for news in company.recent_news[:3]:
                            st.write(f"• {news}")
                    
                    if company.key_products:
                        st.caption("Key Products")
                        st.write(", ".join(company.key_products[:5]))
                    
                    if company.recent_funding:
                        st.caption("Recent Funding")
                        st.write(company.recent_funding)
                    
                    # Generate email if requested
                    if generate_email_check:
                        with st.spinner("Generating email..."):
                            email = email_generator.generate_email(company)
                            st.subheader("📧 Outreach Email")
                            st.text(f"Subject: {email.subject}")
                            st.text_area("Email Body", email.body, height=300)
                            st.success(f"CTA: {email.call_to_action}")
                            st.caption("Personalization Points: " + ", ".join(email.personalization_points))
            else:
                st.warning("Please enter a company name.")
    
    else:  # CSV Upload
        uploaded_file = st.file_uploader("Upload CSV with company names", type=['csv'])
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            # Check for company column
            if 'company' in df.columns or 'company_name' in df.columns:
                company_col = 'company' if 'company' in df.columns else 'company_name'
                companies = df[company_col].tolist()
                
                st.write(f"Found {len(companies)} companies to process.")
                st.dataframe(df.head())
                
                if st.button("🚀 Process Batch", type="primary"):
                    with st.spinner(f"Processing {len(companies)} companies..."):
                        results = enricher.enrich_batch(companies)
                        
                        # Display results
                        success_count = sum(1 for r in results if r.company)
                        cache_hits = sum(1 for r in results if r.from_cache)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Companies", len(results))
                        col2.metric("Success", success_count)
                        col3.metric("Cache Hits", cache_hits)
                        
                        # Create results dataframe
                        result_data = []
                        for r in results:
                            if r.company:
                                result_data.append({
                                    'Company': r.company.company_name,
                                    'Industry': r.company.industry,
                                    'CEO': r.company.ceo,
                                    'Employees': r.company.employee_count,
                                    'Founded': r.company.founded_year,
                                    'Cache': "✅" if r.from_cache else "❌",
                                    'Latency': f"{r.processing_time_ms:.0f}ms"
                                })
                        
                        result_df = pd.DataFrame(result_data)
                        st.dataframe(result_df)
                        
                        # Download button
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results",
                            data=csv,
                            file_name="enriched_companies.csv",
                            mime="text/csv"
                        )
            else:
                st.error("CSV must contain a 'company' or 'company_name' column.")

with tab2:
    st.subheader("Generate Outreach Emails")
    
    # Load enriched companies
    st.info("Enter a company name to generate a personalized email.")
    company_name = st.text_input("Company Name", key="email_company")
    
    if st.button("📧 Generate Email", type="primary"):
        if company_name:
            # Try to get from cache first
            cached = cache.get(company_name)
            if cached:
                company = CompanyInfo(**cached)
                email = email_generator.generate_email(company)
                
                st.success(f"✅ Email generated for {company_name}")
                st.text(f"Subject: {email.subject}")
                st.text_area("Email Body", email.body, height=350)
                st.success(f"CTA: {email.call_to_action}")
                st.caption("Personalization Points: " + ", ".join(email.personalization_points))
            else:
                # Enrich first, then generate email
                with st.spinner(f"Enriching {company_name} first..."):
                    result = enricher.enrich_company(company_name)
                    if result.company:
                        email = email_generator.generate_email(result.company)
                        st.success(f"✅ Email generated for {company_name}")
                        st.text(f"Subject: {email.subject}")
                        st.text_area("Email Body", email.body, height=350)
                        st.success(f"CTA: {email.call_to_action}")
                    else:
                        st.error(f"Could not enrich {company_name}")
        else:
            st.warning("Please enter a company name.")

with tab3:
    st.subheader("📊 Analytics")
    
    # Cache analytics
    st.markdown("### 💾 Cache Performance")
    stats = cache.get_cache_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cached", stats['total_cached'])
    col2.metric("Fresh", stats['fresh_cached'])
    col3.metric("Stale", stats['stale_cached'])
    col4.metric("TTL", f"{stats['ttl_hours']}h")
    
    # Cost savings estimate
    if stats['fresh_cached'] > 0:
        cost_saved = stats['fresh_cached'] * 0.002  # $0.002 per company
        st.metric("💰 Estimated Cost Saved", f"${cost_saved:.3f}", delta="API calls avoided")
    
    st.markdown("### 📋 Recent Activity")
    st.info("Run the enrichment pipeline to see activity here.")

    # In the sidebar
if st.button("🎯 Load Sample Companies"):
    st.session_state['sample_data'] = pd.read_csv("data/sample_companies.csv")
    st.rerun()