#  B2B Lead Enrichment Engine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-orange.svg)](https://openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-Search-green.svg)](https://tavily.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-Cache-blue.svg)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Automated B2B lead enrichment with cost-optimized caching and personalized email generation.**

---

##  What This Does

This tool enriches company data from a CSV or single input, extracts key information (industry, leadership, recent news, products, funding), and generates personalized outreach emails, all while **saving API costs** with a built‑in SQLite cache.

| Feature | Description |
|---------|-------------|
|  **Company Input** | Single company or bulk CSV upload |
|  **Web Enrichment** | Uses Tavily search + OpenAI to extract structured data |
|  **Smart Caching** | SQLite cache with TTL to avoid duplicate API calls |
|  **Email Generation** | Creates personalized cold outreach emails |
|  **Cost Tracking** | Shows estimated cost per enrichment |
|  **Web Interface** | Clean Streamlit dashboard |

---

##  Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.11+ | Core logic |
| **LLM** | OpenAI GPT-4o-mini | Entity extraction & email generation |
| **Search API** | Tavily | Real‑time web search |
| **Caching** | SQLite | Local cache with TTL (7 days) |
| **Data Validation** | Pydantic | Structured output validation |
| **Web UI** | Streamlit | Interactive dashboard |
| **Logging** | Custom rolling logger | Production‑grade logging |

---

##  Architecture


┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ CSV/Input │────▶│ Streamlit UI │────▶│ Cache Check │
│ (Companies) │ │ (Dashboard) │ │ (SQLite) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐
│ Enrichment │
│ Agent │
│ (Tavily+LLM) │
└─────────────────┘
│
▼
┌─────────────────┐
│ Pydantic │
│ Validation │
└─────────────────┘
│
▼
┌─────────────────┐
│ Email │
│ Generator │
└─────────────────┘



---

##  Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Tavily API key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/lead-enrichment-engine.git
cd lead-enrichment-engine

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys


Run the Dashboard
streamlit run dashboard.py
Open http://localhost:8501 in your browser.


Usage
1. Single Company Enrichment
Enter a company name (e.g., Microsoft).

Click Enrich.

View the extracted data: industry, CEO, recent news, key products, etc.

2. Bulk CSV Upload
Upload a CSV with a company or company_name column.

Click Process Batch.

Download the enriched results as a new CSV.

3. Generate Outreach Email
Enrich a company.

Check "Also generate outreach email".

A personalized email draft will appear.


Caching & Cost Control
Every enrichment result is stored in SQLite with a 7‑day TTL.

Subsequent searches for the same company are served from the cache.

Cost savings: ~40‑60% reduction in API calls.

Metric	Value
Cache TTL	7 days
Estimated cost per enrichment	$0.002
Typical cache hit rate	> 50%


Sample Output
Enriched Company Data
{
  "company_name": "Microsoft",
  "industry": "Technology",
  "employee_count": "200,000+",
  "founded_year": "1975",
  "ceo": "Satya Nadella",
  "recent_news": [
    "Microsoft announces new AI features for Office 365",
    "Microsoft reports 20% revenue growth in Q3"
  ],
  "key_products": ["Azure", "Office 365", "Windows"],
  "recent_funding": "N/A"
}


Outreach Email
Subject: AI-driven insights for Microsoft
Body:
Hi Satya,
I've been following Microsoft's recent AI announcements. I help companies like yours leverage AI for lead generation.
Would you be open to a 15‑minute call next week?
CTA: Reply to schedule.


Configuration
Variable	Description	Default
OPENAI_API_KEY	OpenAI API key	(required)
TAVILY_API_KEY	Tavily API key	(required)
CACHE_TTL_SECONDS	Cache TTL in seconds	7 days
MAX_SEARCH_RESULTS	Max Tavily results	5
MAX_CONTENT_CHARS	Truncation limit	4000


Testing
# Run unit tests
pytest tests/

# Test enrichment locally
python test_enricher.py


Docker Deployment
docker build -t lead-enrichment .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... -e TAVILY_API_KEY=tvly-... lead-enrichment


Project Structure
lead-enrichment-engine/
├── .env.example          # Template for secrets
├── .gitignore
├── README.md
├── requirements.txt
├── config.py             # Configuration
├── logger.py             # Production logging
├── models.py             # Pydantic models
├── cache.py              # SQLite caching
├── enricher.py           # Core enrichment logic
├── email_generator.py    # Outreach email generation
├── dashboard.py          # Streamlit UI
├── run_pipeline.py       # Batch processing
├── data/
│   ├── cache.db          # SQLite cache (auto-created)
│   └── output/           # Enriched CSVs
└── tests/
    └── test_enricher.py


Future Enhancements
Add support for HubSpot and Salesforce integration

Add AI‑generated follow‑up emails

Real‑time Slack alerts for new leads

Support for more data sources (LinkedIn, Crunchbase)


License
MIT – Feel free to use for your own projects!

Built as part of an AI/ML portfolio project.
