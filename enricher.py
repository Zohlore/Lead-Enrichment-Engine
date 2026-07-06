import os
import json
import re
import time
from typing import List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tavily import TavilyClient

from models import CompanyInfo, EnrichmentResult
from cache import cache
from logger import logger

load_dotenv()  # for local development

# ------------------------------------------------------------------
# Helper to get API keys (works on both Streamlit Cloud and local)
# ------------------------------------------------------------------
def get_api_key(key_name: str) -> str:
    """Try st.secrets first (Streamlit Cloud), then os.environ (local)."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except ImportError:
        pass
    return os.getenv(key_name, "")

# ------------------------------------------------------------------
# Constants (to replace config.py usage)
# ------------------------------------------------------------------
MAX_SEARCH_RESULTS = 5
MAX_CONTENT_CHARS = 4000
DELAY_BETWEEN_REQUESTS = 1.0

class CompanyEnricher:
    def __init__(self):
        logger.info("Initializing Company Enricher...")
        
        # Read API keys using the helper
        self.openai_api_key = get_api_key("OPENAI_API_KEY")
        self.tavily_api_key = get_api_key("TAVILY_API_KEY")
        
        if not self.openai_api_key or not self.tavily_api_key:
            raise ValueError("Missing API keys. Please set OPENAI_API_KEY and TAVILY_API_KEY in Streamlit secrets or .env")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=self.openai_api_key
        )
        self.tavily = TavilyClient(api_key=self.tavily_api_key)
        self.agent = self._build_agent()
        logger.info("Enricher initialized successfully")
    
    def _search_web(self, query: str) -> str:
        """Search the web for information on a given topic."""
        logger.info(f"🔍 Searching: {query}")
        try:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=MAX_SEARCH_RESULTS
            )
            results = response.get('results', [])
            
            if not results:
                return "No results found."
            
            formatted = []
            for r in results[:MAX_SEARCH_RESULTS]:
                content = r.get('content', '')[:MAX_CONTENT_CHARS]
                formatted.append(
                    f"Title: {r.get('title', 'No title')}\n"
                    f"Content: {content}\n"
                    f"URL: {r.get('url', '')}\n"
                )
            
            result_str = "\n\n".join(formatted)
            logger.info(f"✅ Found {len(results)} results")
            return result_str
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Error: {e}"
    
    def _build_agent(self):
        """Build the agent using LangGraph's create_react_agent."""
        logger.debug("Building agent with LangGraph...")
        
        def web_search(query: str) -> str:
            return self._search_web(query)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Searches the web for company information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query about the company"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        system_prompt = """You are a professional business research assistant.

Your goal is to enrich company data with accurate information from the web.

For each company, you MUST search for:
1. Company website, industry, employee count, founded year
2. Key leadership (CEO, CTO, Head of Sales)
3. Recent news (last 6 months)
4. Key products or services
5. Recent funding rounds

**IMPORTANT: You MUST output ONLY a valid JSON object. Do not include any extra text, explanations, or markdown. The JSON must have these exact fields:**

{
    "company_name": "...",
    "website": "...",
    "industry": "...",
    "employee_count": "...",
    "founded_year": "...",
    "ceo": "...",
    "cto": "...",
    "head_of_sales": "...",
    "recent_news": ["...", "..."],
    "key_products": ["...", "..."],
    "recent_funding": "...",
    "source_urls": ["...", "..."]
}

Use the search results to fill in the data. If a field is unknown, use null."""
        
        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
            debug=False
        )
        return agent
    
    def enrich_company(self, company_name: str) -> EnrichmentResult:
        """Enrich a single company."""
        logger.info(f"Enriching: {company_name}")
        start_time = time.time()
        
        # Check cache FIRST (cost control)
        cached = cache.get(company_name)
        if cached:
            logger.info(f"✅ Cache hit for {company_name}")
            company_info = CompanyInfo(**cached)
            return EnrichmentResult(
                company=company_info,
                from_cache=True,
                processing_time_ms=0,
                cost_estimate_usd=0
            )
        
        try:
            # Perform multiple searches
            search_results = {}
            aspects = ["industry", "leadership", "news", "products", "funding"]
            
            for aspect in aspects:
                search_results[aspect] = self._search_company(company_name, aspect)
                time.sleep(0.5)  # Rate limiting
            
            # Build context
            context = f"Company: {company_name}\n\n"
            context += f"INDUSTRY: {search_results.get('industry', '')}\n\n"
            context += f"LEADERSHIP: {search_results.get('leadership', '')}\n\n"
            context += f"RECENT NEWS: {search_results.get('news', '')}\n\n"
            context += f"PRODUCTS: {search_results.get('products', '')}\n\n"
            context += f"FUNDING: {search_results.get('funding', '')}\n\n"
            
            # Use OpenAI to extract structured data
            system_prompt = """Extract company information from the following text and return as JSON.

The JSON should have these fields:
- company_name: string
- website: string or null
- industry: string or null
- employee_count: string or null
- founded_year: string or null
- ceo: string or null
- cto: string or null
- head_of_sales: string or null
- recent_news: array of strings (max 5)
- key_products: array of strings (max 5)
- recent_funding: string or null
- source_urls: array of strings (max 5)

Return ONLY valid JSON, no other text."""
            
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Company: {company_name}\n\nSearch Results:\n{context}"}
            ])
            
            output = response.content
            
            # Try multiple ways to extract JSON
            json_str = None
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                # Try to find JSON between code fences
                code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
                if code_match:
                    json_str = code_match.group(1)
            
            if json_str:
                try:
                    company_dict = json.loads(json_str)
                    # Ensure company_name is set
                    company_dict['company_name'] = company_name
                    company_info = CompanyInfo(**company_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    company_info = CompanyInfo(
                        company_name=company_name,
                        recent_news=["Enrichment completed"],
                        source_urls=[]
                    )
            else:
                logger.warning(f"Could not parse JSON for {company_name}")
                company_info = CompanyInfo(
                    company_name=company_name,
                    recent_news=["Enrichment completed"],
                    source_urls=[]
                )
            
            # Cache the result
            cache.set(company_name, company_info.dict())
            
            processing_time = (time.time() - start_time) * 1000
            
            return EnrichmentResult(
                company=company_info,
                from_cache=False,
                processing_time_ms=processing_time,
                cost_estimate_usd=0.005
            )
            
        except Exception as e:
            logger.error(f"Failed to enrich {company_name}: {e}")
            company_info = CompanyInfo(
                company_name=company_name,
                recent_news=[f"Error during enrichment"],
                source_urls=[]
            )
            return EnrichmentResult(
                company=company_info,
                from_cache=False,
                processing_time_ms=(time.time() - start_time) * 1000,
                cost_estimate_usd=0
            )
    
    def _search_company(self, company_name: str, aspect: str) -> str:
        """Search for a specific aspect of a company."""
        query = f"{company_name} {aspect}"
        return self._search_web(query)
    
    def enrich_batch(self, company_names: List[str]) -> List[EnrichmentResult]:
        """Enrich a batch of companies."""
        results = []
        total = len(company_names)
        
        logger.info(f"Processing {total} companies...")
        
        for i, name in enumerate(company_names, 1):
            logger.info(f"Progress: {i}/{total}")
            result = self.enrich_company(name)
            results.append(result)
            
            if i < total:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        cache_hits = sum(1 for r in results if r.from_cache)
        logger.info(f"✅ Batch complete. Cache hits: {cache_hits}/{total}")
        
        return results

# Global enricher instance
enricher = CompanyEnricher()