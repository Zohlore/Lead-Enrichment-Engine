from enricher import enricher

result = enricher.enrich_company("Microsoft")

if result.company:
    print("✅ Success!")
    print("Company:", result.company.company_name)
    print("Industry:", result.company.industry)
    print("CEO:", result.company.ceo)
    print("From cache:", result.from_cache)
else:
    print("❌ Failed to enrich")
    print("Error:", result.error if hasattr(result, 'error') else "No error info")