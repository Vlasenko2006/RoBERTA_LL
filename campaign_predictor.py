import os
from groq import Groq
import logging
import json

logger = logging.getLogger(__name__)

# Business reasoning rules (embedded for RAG)
BUSINESS_RULES = """
# Business Reasoning Rules for Campaign Strategy Analysis

## Key Rules:

1. **Discount Strategy**: 20-30% off increases volume 30-60% but reduces margin 15-25%. ROI: (New Customers × AOV × Margin) - Discount Cost > Current Revenue

2. **Free Items**: Low-cost items (drinks) have high perceived value ($5-10) but low actual cost ($1-3). Conversion: 40-70% become paying customers.

3. **Loyalty Programs**: 
   - 2-3 visits: 70-80% completion
   - 5 visits: 40-50% completion
   - 10+ visits: 15-25% completion
   Customers completing 5+ visits have 3x lifetime value.

4. **Urgency Tactics**: "Today only" boosts conversion 200-300% but damages trust if overused (>2x/month).

5. **Price Positioning**: If positive reviews mention "quality"/"premium", avoid discounts. If negative mentions "expensive", use value bundles.

6. **Complaint Response**: Address top complaints directly = 40-60% sentiment improvement.

7. **Amplify Positives**: Feature what customers already love. Leverage strengths > fix weaknesses.

8. **Bundle Strategy**: Perceived discount 20% but actual margin impact 5-10%. Increases AOV by 30-40%.

9. **First-Time vs Return**: New customers need risk reduction. Loyal customers want rewards.

10. **ROI Threshold**: Customer Lifetime Value must be >3× Customer Acquisition Cost for sustainable growth.

11. **Social Proof**: High positive sentiment + testimonials = 50-100% effectiveness boost.

12. **Cumulative Effect**: Short-term revenue + long-term habit formation. Loyalty programs: 4-5x ROI over 12 months.
"""

def predict_campaign_variants(variants: list, language: str = 'en', job_id: str = None):
    """
    Analyze campaign strategies using LLaMA 3.3 with business reasoning.
    
    Args:
        variants: List of campaign strategy texts
        language: Language code (de/en) - both supported by LLaMA
        job_id: Optional job ID to retrieve sentiment summary for context
    
    Returns:
        dict with analysis and recommendations
    """
    try:
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Load sentiment summary if job_id provided
        sentiment_context = ""
        if job_id:
            try:
                trends_path = f"my_volume/sentiment_analysis/{job_id}/sentiment_trends.json"
                if os.path.exists(trends_path):
                    with open(trends_path, 'r') as f:
                        trends = json.load(f)
                    summary = trends.get('summary', {})
                    
                    total_positive = summary.get('total_positive', 0)
                    total_negative = summary.get('total_negative', 0)
                    total_neutral = summary.get('total_neutral', 0)
                    total = total_positive + total_negative + total_neutral
                    
                    if total > 0:
                        sentiment_context = f"""
CUSTOMER SENTIMENT SUMMARY (from actual analysis):
- Positive: {total_positive} ({(total_positive/total*100):.1f}%) 
  Key themes: {summary.get('positive_keywords', 'N/A')}
- Negative: {total_negative} ({(total_negative/total*100):.1f}%)
  Key themes: {summary.get('negative_keywords', 'N/A')}
- Neutral: {total_neutral} ({(total_neutral/total*100):.1f}%)

Top positive comments: {summary.get('positive_summary', 'Great service, quality food')}
Top complaints: {summary.get('negative_summary', 'Prices, wait times')}
"""
            except Exception as e:
                logger.warning(f"Could not load sentiment data: {e}")
        
        if not sentiment_context:
            sentiment_context = """
CUSTOMER SENTIMENT SUMMARY: 
No analysis data available. Using general business reasoning only.
"""
        
        # Analyze each variant
        analyses = []
        
        for i, strategy in enumerate(variants, 1):
            prompt = f"""You are a business strategist analyzing marketing campaign strategies based on customer sentiment data and business reasoning rules.

{sentiment_context}

BUSINESS REASONING RULES:
{BUSINESS_RULES}

PROPOSED STRATEGY #{i}:
"{strategy}"

ANALYSIS REQUIRED:
1. Sentiment Alignment: Does this strategy address customer complaints or leverage positive feedback?
2. Business Rules: Which rules apply? What's the expected impact?
3. ROI Projection: Will this increase revenue considering costs?
4. Risks: What could go wrong? (brand dilution, low completion, etc.)
5. Score: Rate 1-10 (10 = excellent strategy)
6. Recommendation: How to improve this strategy?

Provide analysis in this JSON format:
{{
  "score": 7.5,
  "sentiment_alignment": "Addresses price concerns but doesn't leverage quality reviews",
  "business_rules_applied": ["Rule 3: Loyalty programs", "Rule 1: Discount strategy"],
  "roi_projection": "40-50% volume increase, 25% margin reduction, 2.1x ROI over 6 months",
  "risks": ["5-visit requirement = only 40% completion rate", "May attract deal-seekers not loyal customers"],
  "recommendation": "Reduce to 3 visits OR increase reward to 40% off to improve completion rate",
  "reasoning": "Detailed explanation of why this score was given"
}}

Respond ONLY with valid JSON, no additional text."""

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                if "```json" in analysis_text:
                    analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
                elif "```" in analysis_text:
                    analysis_text = analysis_text.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(analysis_text)
                
                analyses.append({
                    'text': strategy,
                    'score': analysis.get('score', 5.0),
                    'sentiment_alignment': analysis.get('sentiment_alignment', ''),
                    'business_rules_applied': analysis.get('business_rules_applied', []),
                    'roi_projection': analysis.get('roi_projection', ''),
                    'risks': analysis.get('risks', []),
                    'recommendation': analysis.get('recommendation', ''),
                    'reasoning': analysis.get('reasoning', '')
                })
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLaMA response as JSON: {e}\nResponse: {analysis_text}")
                # Fallback: provide basic analysis
                analyses.append({
                    'text': strategy,
                    'score': 5.0,
                    'sentiment_alignment': 'Could not analyze',
                    'business_rules_applied': [],
                    'roi_projection': 'Unknown',
                    'risks': ['Analysis failed'],
                    'recommendation': 'Try rephrasing the strategy',
                    'reasoning': analysis_text[:200]
                })
        
        # Sort by score (highest first)
        sorted_analyses = sorted(analyses, key=lambda x: x['score'], reverse=True)
        best_strategy = sorted_analyses[0]
        
        return {
            'predictions': analyses,
            'best_variant': best_strategy,
            'total_analyzed': len(variants),
            'analysis_method': 'LLaMA 3.3 Business Reasoning + Customer Sentiment'
        }
        
    except Exception as e:
        logger.error(f"Error analyzing campaign variants: {e}")
        raise Exception(f"Campaign analysis failed: {str(e)}")
