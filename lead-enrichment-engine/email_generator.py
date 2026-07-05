import json
import re
from typing import Optional
from openai import OpenAI
from models import CompanyInfo, OutreachEmail
from logger import logger
from config import config

class EmailGenerator:
    """Generate personalized outreach emails using OpenAI directly (no LangChain)."""
    
    def __init__(self):
        logger.info("Initializing Email Generator...")
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL
        logger.info("Email Generator initialized")
    
    def generate_email(self, company: CompanyInfo, target_role: str = "CEO") -> OutreachEmail:
        """Generate a personalized outreach email."""
        logger.info(f"Generating email for {company.company_name}")
        
        # Build personalization context
        context_parts = []
        if company.ceo:
            context_parts.append(f"CEO: {company.ceo}")
        if company.cto:
            context_parts.append(f"CTO: {company.cto}")
        if company.head_of_sales:
            context_parts.append(f"Head of Sales: {company.head_of_sales}")
        if company.recent_news:
            context_parts.append(f"Recent news: {'; '.join(company.recent_news[:2])}")
        if company.recent_funding:
            context_parts.append(f"Recent funding: {company.recent_funding}")
        if company.key_products:
            context_parts.append(f"Products: {', '.join(company.key_products[:3])}")
        if company.industry:
            context_parts.append(f"Industry: {company.industry}")
        
        context_str = "\n".join(context_parts) if context_parts else "Limited information available."
        
        # Build the prompt
        system_prompt = """You are a professional B2B sales copywriter specializing in cold outreach.

Generate a personalized cold email for a sales development representative.

Rules:
1. Personalized opening (mention company/role)
2. 2-3 sentences showing you've researched them
3. Clear value proposition
4. Specific call to action
5. Professional but friendly tone
6. Max 200 words

Format the response as valid JSON with these fields:
- subject: email subject line
- body: email body
- call_to_action: clear CTA statement
- personalization_points: list of insights used"""

        user_prompt = f"""Write a cold outreach email to {company.company_name}.

Company Context:
{context_str}

Target recipient: {target_role}
Goal: Schedule a 15-minute discovery call about AI lead generation

Return ONLY valid JSON."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            output = response.choices[0].message.content
            
            # Extract JSON from output
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                email_dict = json.loads(json_match.group())
                return OutreachEmail(**email_dict)
            else:
                logger.warning("No JSON found, using fallback")
                return self._fallback_email(company)
                
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            return self._fallback_email(company)
    
    def _fallback_email(self, company: CompanyInfo) -> OutreachEmail:
        """Fallback email generation if API fails."""
        ceo_name = company.ceo or "there"
        return OutreachEmail(
            subject=f"AI-driven insights for {company.company_name}",
            body=f"""Hi {ceo_name},

I've been researching {company.company_name} and noticed your work in {company.industry or 'your industry'}.

I help companies like yours leverage AI to generate qualified leads and streamline their sales process. I'd love to share how we've helped similar organizations achieve 3x ROI in just 30 days.

Would you be open to a 15-minute discovery call next week?

Best regards,
[Your Name]""",
            call_to_action="Reply to schedule a 15-minute discovery call.",
            personalization_points=["Company research", f"Industry: {company.industry or 'N/A'}"]
        )

# Global email generator
email_generator = EmailGenerator()