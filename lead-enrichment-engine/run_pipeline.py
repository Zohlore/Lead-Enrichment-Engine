# Batch processing
import pandas as pd
from datetime import datetime
from enricher import enricher
from logger import logger

def process_csv(input_file: str, output_file: str = None):
    """Process a CSV of companies."""
    logger.info(f"Processing: {input_file}")
    
    # Read input
    df = pd.read_csv(input_file)
    company_col = 'company' if 'company' in df.columns else 'company_name'
    
    if company_col not in df.columns:
        logger.error(f"No 'company' or 'company_name' column found")
        return
    
    companies = df[company_col].tolist()
    logger.info(f"Found {len(companies)} companies")
    
    # Enrich
    results = enricher.enrich_batch(companies)
    
    # Create output
    output_data = []
    for r in results:
        if r.company:
            output_data.append({
                'company': r.company.company_name,
                'industry': r.company.industry,
                'ceo': r.company.ceo,
                'employee_count': r.company.employee_count,
                'founded_year': r.company.founded_year,
                'recent_news': '; '.join(r.company.recent_news[:3]),
                'key_products': '; '.join(r.company.key_products[:3]),
                'from_cache': r.from_cache,
                'latency_ms': r.processing_time_ms,
                'cost_usd': r.cost_estimate_usd
            })
    
    output_df = pd.DataFrame(output_data)
    
    # Save
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/output/enriched_{timestamp}.csv"
    
    output_df.to_csv(output_file, index=False)
    logger.info(f"✅ Saved {len(output_data)} records to {output_file}")
    
    return output_df

if __name__ == "__main__":
    # Example usage
    process_csv("data/input/companies.csv")