"""
Video Script Generator for Marketing Campaigns
Uses LLaMA 3.3 via Groq API to generate video scripts AND image prompts from sentiment analysis
"""

import json
import os
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_video_script(job_id: str, language: str = "de", duration: int = 30) -> dict:
    """
    Generate a video script AND image generation prompts based on sentiment analysis
    
    Args:
        job_id: Job ID to get analysis results
        language: Target language (de or en)
        duration: Video duration in seconds (default 30)
    
    Returns:
        Dictionary with hook, key_messages, call_to_action, visual_suggestions, image_prompts
    """
    
    # Load sentiment analysis results
    results_path = f"my_volume/sentiment_analysis/{job_id}/sentiment_trends.json"
    performance_path = f"my_volume/sentiment_analysis/{job_id}/performance_summary.json"
    
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"No results found for job_id: {job_id}")
    
    # Try to load performance summary for more accurate stats
    try:
        with open(performance_path, 'r', encoding='utf-8') as f:
            performance_data = json.load(f)
            sentiment_dist = performance_data.get('sentiment_distribution', {})
            total_reviews = performance_data.get('total_samples', 0)
            positive_count = sentiment_dist.get('POSITIVE', 0)
            negative_count = sentiment_dist.get('NEGATIVE', 0)
            neutral_count = sentiment_dist.get('NEUTRAL', 0)
            positive_pct = round((positive_count / total_reviews * 100) if total_reviews > 0 else 0, 1)
            negative_pct = round((negative_count / total_reviews * 100) if total_reviews > 0 else 0, 1)
    except:
        # Fallback to sentiment_trends.json
        summary = sentiment_data.get('summary', {})
        total_reviews = summary.get('total_reviews', 0)
        positive_pct = summary.get('positive_percentage', 0)
        negative_pct = summary.get('negative_percentage', 0)
    
    # Get top positive and negative themes from trends
    trends = sentiment_data.get('trends', [])
    top_positive_themes = []
    top_negative_themes = []
    
    for trend in trends[:10]:  # Look at recent trends
        sentiment = trend.get('sentiment', '')
        comment = trend.get('representative_comment', '')
        if sentiment == 'positive' and comment and len(top_positive_themes) < 3:
            top_positive_themes.append(comment[:100])  # First 100 chars
        elif sentiment == 'negative' and comment and len(top_negative_themes) < 2:
            top_negative_themes.append(comment[:100])
    
    # Build context for LLaMA
    context = f"""
Analysis Summary:
- Total Reviews: {total_reviews}
- Positive: {positive_pct}%
- Negative: {negative_pct}%

Top Positive Themes:
{chr(10).join(f"- {theme}" for theme in top_positive_themes[:3])}

Areas for Improvement:
{chr(10).join(f"- {theme}" for theme in top_negative_themes[:2])}
"""
    
    # Create enhanced prompt for video script AND image prompts generation
    if language == "de":
        prompt = f"""Du bist ein kreativer Video-Marketing-Experte. Erstelle basierend auf dieser Sentiment-Analyse einen {duration}-Sekunden Video-Script UND 4 Bild-Generierungs-Prompts für KI-Bildmodelle (Stable Diffusion):

{context}

Erstelle eine fesselnde 4-Stufen-Werbestory:

1. VIDEO SCRIPT:
   - HOOK (0-5s): Aufmerksamkeitsstarke Eröffnung
   - KEY MESSAGES (5-20s): 3 überzeugende Botschaften aus positiven Themen
   - CALL-TO-ACTION (20-25s): Klare Handlungsaufforderung
   - VISUAL SUGGESTIONS: 4-5 visuelle Element-Vorschläge

2. IMAGE PROMPTS (für Stable Diffusion):
   Erstelle 4 DETAILLIERTE, VISUELLE Prompts die:
   - Spannend und fesselnd sind
   - Leicht für KI-Bildmodelle zu interpretieren
   - Die Story visuell erzählen
   - Spezifische visuelle Elemente, Farben, Stimmung enthalten
   - Auf echten Review-Themen basieren
   
   Format für jeden Prompt:
   - Hook: [Detaillierter englischer Prompt für Bildgenerierung, 50-100 Wörter]
   - Key_Messages: [Detaillierter englischer Prompt für Bildgenerierung, 50-100 Wörter]
   - CTA: [Detaillierter englischer Prompt für Bildgenerierung, 50-100 Wörter]
   - Visuals: [Detaillierter englischer Prompt für Bildgenerierung, 50-100 Wörter]

WICHTIG: Bild-Prompts müssen auf ENGLISCH sein (Stable Diffusion versteht Englisch am besten).
Verwende beschreibende Begriffe wie: "professional photography", "modern design", "warm lighting", 
"vibrant colors", "clean composition", "high quality", etc.

Format: JSON
{{
  "hook": "Wussten Sie, dass {positive_pct}% unserer Gäste begeistert sind?",
  "key_messages": [
    "Authentische Küche - Frische aus der Region",
    "Herzlicher Service - Sie fühlen sich wie zuhause",
    "Gemütliche Atmosphäre - Perfekt für jeden Anlass"
  ],
  "call_to_action": "Reservieren Sie heute Ihren Tisch - Erleben Sie den Unterschied!",
  "visual_suggestions": [
    "Glückliche Gäste beim Essen zeigen",
    "Statistik-Animation: {positive_pct}% Zufriedenheit",
    "Authentische Gerichte in Nahaufnahme",
    "Gemütliches Restaurant-Interieur",
    "Logo mit Reservierungs-Button"
  ],
  "image_prompts": {{
    "hook": "Professional photo of diverse happy restaurant customers smiling and raising glasses in toast, warm ambient lighting, authentic German cuisine visible on table, five star rating icons floating above, cozy restaurant interior background, candid moment captured, high quality commercial food photography, inviting atmosphere, golden hour lighting, shallow depth of field",
    "key_messages": "Three panel composition showing: left panel with steaming authentic German dish in close-up food photography style, center panel with friendly chef and server smiling warmly while presenting dish, right panel showing cozy restaurant interior with soft lighting and comfortable seating, warm color palette, professional restaurant photography, welcoming atmosphere, modern rustic style",
    "cta": "Modern restaurant booking interface design, glowing RESERVE TABLE button in center, calendar showing today's date highlighted in blue, fork and knife icons, special badge showing 'Join {positive_count} Happy Diners', warm inviting colors matching restaurant brand, clean UI design, professional web interface, sense of urgency and excitement, call-to-action focused composition",
    "visuals": "Professional business infographic showing {positive_pct}% satisfaction rate in large bold numbers, grid mosaic of {positive_count} happy customer faces smiling, five gold stars prominently displayed, upward trending graph line, restaurant logo, authentic German cuisine elements as decorative accents, warm professional color scheme, modern data visualization style, trustworthy and credible design"
  }}
}}

Gib NUR das JSON zurück, keine zusätzlichen Erklärungen."""
    else:  # English
        prompt = f"""You are a creative video marketing expert. Based on this sentiment analysis, create a {duration}-second video script AND 4 image generation prompts for AI image models (Stable Diffusion):

{context}

Create a thrilling 4-stage advertising story:

1. VIDEO SCRIPT:
   - HOOK (0-5s): Attention-grabbing opening
   - KEY MESSAGES (5-20s): 3 compelling messages from positive themes
   - CALL-TO-ACTION (20-25s): Clear action request
   - VISUAL SUGGESTIONS: 4-5 visual element suggestions

2. IMAGE PROMPTS (for Stable Diffusion):
   Create 4 DETAILED, VISUAL prompts that are:
   - Thrilling and capturing
   - Easy for AI image models to interpret
   - Tell the story visually
   - Include specific visual elements, colors, mood
   - Based on actual review themes
   
   Format for each prompt:
   - Hook: [Detailed English prompt for image generation, 50-100 words]
   - Key_Messages: [Detailed English prompt for image generation, 50-100 words]
   - CTA: [Detailed English prompt for image generation, 50-100 words]
   - Visuals: [Detailed English prompt for image generation, 50-100 words]

Use descriptive terms like: "professional photography", "modern design", "warm lighting", 
"vibrant colors", "clean composition", "high quality", "cinematic", etc.

Format: JSON
{{
  "hook": "Did you know {positive_pct}% of our guests are thrilled?",
  "key_messages": [
    "Authentic cuisine - Fresh regional ingredients",
    "Warm service - Feel right at home",
    "Cozy atmosphere - Perfect for any occasion"
  ],
  "call_to_action": "Reserve your table today - Experience the difference!",
  "visual_suggestions": [
    "Show happy diners enjoying meals",
    "Animated statistics: {positive_pct}% satisfaction",
    "Close-up of authentic dishes",
    "Cozy restaurant interior",
    "Logo with reservation button"
  ],
  "image_prompts": {{
    "hook": "Professional photo of diverse happy restaurant customers smiling and raising glasses in toast, warm ambient lighting, authentic German cuisine visible on table, five star rating icons floating above, cozy restaurant interior background, candid moment captured, high quality commercial food photography, inviting atmosphere, golden hour lighting, shallow depth of field",
    "key_messages": "Three panel composition showing: left panel with steaming authentic German dish in close-up food photography style, center panel with friendly chef and server smiling warmly while presenting dish, right panel showing cozy restaurant interior with soft lighting and comfortable seating, warm color palette, professional restaurant photography, welcoming atmosphere, modern rustic style",
    "cta": "Modern restaurant booking interface design, glowing RESERVE TABLE button in center, calendar showing today's date highlighted in blue, fork and knife icons, special badge showing 'Join {positive_count} Happy Diners', warm inviting colors matching restaurant brand, clean UI design, professional web interface, sense of urgency and excitement, call-to-action focused composition",
    "visuals": "Professional business infographic showing {positive_pct}% satisfaction rate in large bold numbers, grid mosaic of {positive_count} happy customer faces smiling, five gold stars prominently displayed, upward trending graph line, restaurant logo, authentic German cuisine elements as decorative accents, warm professional color scheme, modern data visualization style, trustworthy and credible design"
  }}
}}

Return ONLY the JSON, no additional explanations."""
    
    # Call LLaMA via Groq
    if not client:
        # Fallback if Groq is not configured
        return {
            "hook": "Discover what our customers are saying!",
            "key_messages": [
                f"Over {positive_pct}% positive customer feedback",
                "Join thousands of satisfied customers",
                "Experience the difference yourself"
            ],
            "call_to_action": "Start your journey today - risk-free trial!",
            "visual_suggestions": [
                "Show customer testimonials",
                "Display satisfaction statistics",
                "Highlight key product features",
                "Include trust badges",
                "End with strong brand logo"
            ],
            "image_prompts": {
                "hook": "happy customers smiling thumbs up five stars",
                "key_messages": "quality badge delivery truck customer service",
                "cta": "blue button shopping cart click here",
                "visuals": f"{positive_pct}% statistics dashboard delivery van"
            }
        }
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional marketing copywriter and creative director specializing in video scripts and visual storytelling. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,  # Slightly higher for more creative prompts
            max_tokens=2000   # Increased for longer image prompts
        )
        
        # Parse response
        script_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case there's extra text)
        if "```json" in script_text:
            script_text = script_text.split("```json")[1].split("```")[0].strip()
        elif "```" in script_text:
            script_text = script_text.split("```")[1].split("```")[0].strip()
        
        script_data = json.loads(script_text)
        
        # Ensure image_prompts exists
        if "image_prompts" not in script_data:
            script_data["image_prompts"] = {
                "hook": "happy customers smiling satisfaction",
                "key_messages": "quality service delivery features",
                "cta": "call to action button interface",
                "visuals": f"{positive_pct}% statistics data visualization"
            }
        
        return script_data
        
    except Exception as e:
        print(f"Error generating video script with LLaMA: {e}")
        # Return fallback script
        return {
            "hook": "Entdecken Sie, was unsere Kunden sagen!" if language == "de" else "Discover what our customers are saying!",
            "key_messages": [
                f"Über {positive_pct}% positive Kundenbewertungen" if language == "de" else f"Over {positive_pct}% positive customer feedback",
                "Werden Sie Teil tausender zufriedener Kunden" if language == "de" else "Join thousands of satisfied customers",
                "Erleben Sie den Unterschied selbst" if language == "de" else "Experience the difference yourself"
            ],
            "call_to_action": "Starten Sie noch heute - risikofreier Test!" if language == "de" else "Start your journey today - risk-free trial!",
            "visual_suggestions": [
                "Kundenbewertungen zeigen" if language == "de" else "Show customer testimonials",
                "Zufriedenheitsstatistiken anzeigen" if language == "de" else "Display satisfaction statistics",
                "Wichtige Produktmerkmale hervorheben" if language == "de" else "Highlight key product features",
                "Vertrauens-Badges einbinden" if language == "de" else "Include trust badges",
                "Mit starkem Markenlogo enden" if language == "de" else "End with strong brand logo"
            ],
            "image_prompts": {
                "hook": "happy customers smiling thumbs up five stars",
                "key_messages": "quality badge delivery truck customer service",
                "cta": "blue button shopping cart click here",
                "visuals": f"{positive_pct}% statistics dashboard delivery van"
            }
        }
