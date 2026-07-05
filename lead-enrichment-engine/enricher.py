# Core enrichment logic
import time
import re
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tavily import TavilyClient

from models import CompanyInfo, EnrichmentResult
from cache import cache
from logger import logger
from config import config

class CompanyEnricher:
    """Enrich company data using web search and LLM."""
    
    def __init__(self):
        logger.info("Initializing Company Enricher...")
        
        self.openai_api_key = config.OPENAI_API_KEY
        self.tavily_api_key = config.TAVILY_API_KEY
        
        if not self.openai_api_key or not self.tavily_api_key:
            raise ValueError("Missing API keys in .env")
        
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.TEMPERATURE,
            api_key=self.openai_api_key
        )
        
        self.tavily = TavilyClient(api_key=self.tavily_api_key)
        self.agent = self._build_agent()
        logger.info("Enricher initialized successfully")
    
    def _search_web(self, query: str) -> str:
        """Search web for company information."""
        logger.info(f"🔍 Searching: {query}")
        try:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=config.MAX_SEARCH_RESULTS
            )
            results = response.get('results', [])
            
            if not results:
                return "No results found."
            
            formatted = []
            for r in results[:config.MAX_SEARCH_RESULTS]:
                content = r.get('content', '')[:config.MAX_CONTENT_CHARS]
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
        """Build the LangGraph agent."""
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

Format your response as a JSON object with:
- company_name
- website
- industry
- employee_count
- founded_year
- ceo
- cto
- head_of_sales
- recent_news (array of strings)
- key_products (array of strings)
- recent_funding
- source_urls (array of strings)

Be specific and accurate. Use search results."""
        
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
        from_cache = False
        
        # Check cache FIRST (cost control)
        cached = cache.get(company_name)
        if cached:
            from_cache = True
            company_info = CompanyInfo(**cached)
            logger.info(f"✅ Cache hit for {company_name}")
            return EnrichmentResult(
                company=company_info,
                from_cache=True,
                processing_time_ms=0,
                cost_estimate_usd=0
            )
        
        try:
            # Run the agent
            messages = [
                {
                    "role": "user",
                    "content": f"""Research this company thoroughly: {company_name}

Search for:
1. Company overview (industry, size, founded)
2. Leadership team (CEO, CTO, Head of Sales)
3. Recent news and announcements
4. Key products and services
5. Recent funding rounds

Use web_search for EACH aspect. Return a structured JSON output."""
                }
            ]
            
            result = self.agent.invoke({"messages": messages})
            output = result['messages'][-1].content
            
            # Extract JSON from output
            import json
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                company_dict = json.loads(json_str)
                company_info = CompanyInfo(**company_dict)
            else:
                # Fallback: basic info from output
                company_info = CompanyInfo(
                    company_name=company_name,
                    recent_news=["Enrichment completed"],
                    source_urls=["Web search"]
                )
                logger.warning(f"Could not parse JSON for {company_name}")
            
            # Cache the result
            cache.set(company_name, company_info.dict())
            
            processing_time = (time.time() - start_time) * 1000
            
            # Cost estimate (rough)
            cost_estimate = 0.002  # ~$0.002 per company
            
            logger.info(f"✅ Enriched {company_name} in {processing_time:.0f}ms")
            
            return EnrichmentResult(
                company=company_info,
                from_cache=False,
                processing_time_ms=processing_time,
                cost_estimate_usd=cost_estimate
            )
            
        except Exception as e:
            logger.error(f"Failed to enrich {company_name}: {e}")
            
            # Return basic info as fallback
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
    
    def enrich_batch(self, company_names: List[str]) -> List[EnrichmentResult]:
        """Enrich a batch of companies."""
        results = []
        total = len(company_names)
        
        logger.info(f"Processing {total} companies...")
        
        for i, name in enumerate(company_names, 1):
            logger.info(f"Progress: {i}/{total}")
            result = self.enrich_company(name)
            results.append(result)
            
            # Rate limiting delay
            if i < total:
                time.sleep(config.DELAY_BETWEEN_REQUESTS)
        
        # Count cache hits
        cache_hits = sum(1 for r in results if r.from_cache)
        logger.info(f"✅ Batch complete. Cache hits: {cache_hits}/{total}")
        
        return results

# Global enricher instance
enricher = CompanyEnricher()