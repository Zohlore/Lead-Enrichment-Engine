# Pydantic models
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CompanyInfo(BaseModel):
    """Structured company information."""
    company_name: str = Field(description="The full company name")
    website: Optional[str] = Field(default=None, description="Company website URL")
    industry: Optional[str] = Field(default=None, description="Primary industry")
    employee_count: Optional[str] = Field(default=None, description="Approximate employee count")
    founded_year: Optional[str] = Field(default=None, description="Year company was founded")
    
    # Key leadership
    ceo: Optional[str] = Field(default=None, description="CEO or founder name")
    cto: Optional[str] = Field(default=None, description="CTO or head of engineering")
    head_of_sales: Optional[str] = Field(default=None, description="Head of sales or revenue")
    
    # Market signals
    recent_news: List[str] = Field(default_factory=list, description="Recent news headlines")
    key_products: List[str] = Field(default_factory=list, description="Key products or services")
    recent_funding: Optional[str] = Field(default=None, description="Recent funding rounds")
    
    # Enrichment metadata
    enriched_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_urls: List[str] = Field(default_factory=list, description="Sources used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "website": "https://acme.com",
                "industry": "Enterprise Software",
                "employee_count": "500-1000",
                "ceo": "Jane Smith",
                "recent_news": ["Acme Corp raises $50M Series B"],
                "key_products": ["Acme CRM", "Acme Analytics"],
                "recent_funding": "$50M Series B (2026)"
            }
        }

class OutreachEmail(BaseModel):
    """Structured outreach email."""
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    call_to_action: str = Field(description="Call to action statement")
    personalization_points: List[str] = Field(description="Key personalization insights used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "AI-driven lead generation for Acme Corp",
                "body": "Hi Jane, I noticed Acme Corp recently...",
                "call_to_action": "Schedule a 15-minute demo",
                "personalization_points": ["Recent funding round", "Industry focus"]
            }
        }

class EnrichmentResult(BaseModel):
    """Complete enrichment result."""
    company: CompanyInfo
    outreach_email: Optional[OutreachEmail] = None
    from_cache: bool = False
    processing_time_ms: float = 0
    cost_estimate_usd: float = 0