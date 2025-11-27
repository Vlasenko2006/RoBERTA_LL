#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Chatbot for Sentiment Analysis Results with DUAL ROLE
Allows users to ask questions about:
1. Sentiment analysis results (analysis context)
2. Andrey Vlasenko (knowledge base)


@author: andreyvlasenko
"""

import json
import os
from groq import Groq
from typing import Dict, List, Optional, Literal
import logging

logger = logging.getLogger(__name__)

# Try to import sentence_transformers and FAISS 
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    Andrey_KB_AVAILABLE = True
    logger.info("Andrey's knowledge base support enabled (sentence-transformers + FAISS)")
except ImportError:
    Andrey_KB_AVAILABLE = False
    logger.warning("Andrey's knowledge base disabled (install sentence-transformers and faiss-cpu)")


class ResultsChatbot:
    """
    Chatbot with DUAL ROLE:
    1. Sentiment Analysis Expert - answers about analysis results
    2. Andrey Representative - answers about Andrey Vlasenko
    
    Uses RAG (Retrieval-Augmented Generation) for both contexts
    """
    
    def __init__(self, job_id: str, analysis_path: str, groq_api_key: str, 
                 Andrey_kb_path: str = "/app/ANDREYS_KNOWLEDGE_BASE.md"):
        """
        Initialize chatbot with analysis results and Andrey knowledge base
        
        Args:
            job_id: Unique job identifier
            analysis_path: Path to sentiment analysis results
            groq_api_key: Groq API key for LLM
            Andrey_kb_path: Path to Andrey knowledge base markdown file
        """
        self.job_id = job_id
        self.analysis_path = analysis_path
        self.groq_client = Groq(api_key=groq_api_key)
        self.context = self._load_analysis_context()
        self.conversation_history = []
        
        # Initialize Andrey knowledge base (if available)
        self.Andrey_kb_path = Andrey_kb_path
        self.Andrey_chunks = []
        self.Andrey_index = None
        self.embedding_model = None
        
        if Andrey_KB_AVAILABLE and os.path.exists(Andrey_kb_path):
            self._initialize_Andrey_kb()
        
        logger.info(f"Chatbot initialized for job {job_id} with dual-role capabilities")
    
    def _initialize_Andrey_kb(self):
        """Initialize Andrey knowledge base with FAISS indexing"""
        try:
            logger.info(f"Loading Andrey knowledge base from {self.Andrey_kb_path}")
            
            # Load and chunk the knowledge base
            with open(self.Andrey_kb_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by major sections (##)
            sections = content.split('\n## ')
            chunks = []
            
            for i, section in enumerate(sections):
                if i == 0:
                    chunks.append(section.strip())
                else:
                    chunks.append('## ' + section.strip())
            
            # Further split large sections
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > 1000:
                    paragraphs = chunk.split('\n\n')
                    current_chunk = ""
                    for para in paragraphs:
                        if len(current_chunk) + len(para) < 1000:
                            current_chunk += para + "\n\n"
                        else:
                            if current_chunk:
                                final_chunks.append(current_chunk.strip())
                            current_chunk = para + "\n\n"
                    if current_chunk:
                        final_chunks.append(current_chunk.strip())
                else:
                    final_chunks.append(chunk)
            
            self.Andrey_chunks = [c for c in final_chunks if len(c.strip()) > 50]
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            
            # Build FAISS index
            embeddings = self.embedding_model.encode(self.Andrey_chunks, show_progress_bar=False)
            dimension = embeddings.shape[1]
            self.Andrey_index = faiss.IndexFlatL2(dimension)
            self.Andrey_index.add(embeddings.astype('float32'))
            
            logger.info(f"✅ Andrey KB initialized: {len(self.Andrey_chunks)} chunks, {dimension}D vectors")
            
        except Exception as e:
            logger.error(f"Failed to initialize Andrey KB: {e}")
            self.Andrey_chunks = []
            self.Andrey_index = None
    
    def _route_query(self, question: str) -> Literal["Andrey_KB", "PLATFORM"]:
        """
        Determine if question is about Andrey or platform
        
        Returns:
            "Andrey_KB" - Search in Andrey knowledge base
            "PLATFORM" - Use sentiment analysis context
        """
        Andrey_keywords = [
            # Names
            'andrey', 'vlasenko', 
            
            # Personal pronouns (interview context)
            'your background', 'your experience', 'your education', 'your projects',
            'your skills', 'your publications', 'your cv', 'your resume', 'your career',
            'tell me about yourself', 'who are you', 'introduce yourself',
            'who developed', 'who created', 'who built',
            
            # Institutions
            'heidelberg', 'max planck', 'hereon', 'dkrz', 'cen', 'hamburg university',
            'moscow institute', 'mipt',
            
            # Specific projects/algorithms
            'nachmo', 'peffra', 'cozyrag', 'storyteller', 'shortgan', 'fatgan',
            'neuronmuse', 'durak', 'cernn', 'crack_finder',
            
            # Career questions
            'worked at', 'studied at', 'phd', 'dissertation', 'thesis',
            'research experience', 'work experience', 'employment history',
            'achievements', 'awards', 'publications', 'papers published',
            'author of', 'developer of',
            
            # Personal
            'hobbies', 'interests', 'pilot', 'aviation', 'cessna', 'fitness',
            'languages speak', 'german', 'english proficiency'
        ]
        
        question_lower = question.lower()
        
        # Check if question is about the Andrey
        if any(keyword in question_lower for keyword in Andrey_keywords):
            return "Andrey_KB"
        
        return "PLATFORM"
    
    def _retrieve_from_Andrey_kb(self, question: str, top_k: int = 3) -> str:
        """Retrieve relevant chunks from Andrey knowledge base"""
        if not self.Andrey_index or not self.embedding_model:
            return ""
        
        try:
            # Encode query
            query_embedding = self.embedding_model.encode([question])
            
            # Search FAISS index
            distances, indices = self.Andrey_index.search(query_embedding.astype('float32'), top_k)
            
            # Retrieve chunks
            retrieved_chunks = [self.Andrey_chunks[i] for i in indices[0]]
            context = "\n\n---\n\n".join(retrieved_chunks)
            
            logger.info(f"Retrieved {top_k} chunks from Andrey KB (distances: {distances[0]})")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving from Andrey KB: {e}")
            return ""
    
    def _load_analysis_context(self) -> Dict:
        """Load all analysis results as context for the chatbot"""
        context = {
            'job_id': self.job_id,
            'positive': {},
            'negative': {},
            'neutral': {},
            'recommendations': {},
            'trends': {},
            'statistics': {}
        }
        
        try:
            # Load positive sentiment data
            positive_path = os.path.join(self.analysis_path, 'positive')
            if os.path.exists(positive_path):
                context['positive'] = self._load_sentiment_data(positive_path, 'positive')
            
            # Load negative sentiment data
            negative_path = os.path.join(self.analysis_path, 'negative')
            if os.path.exists(negative_path):
                context['negative'] = self._load_sentiment_data(negative_path, 'negative')
            
            # Load neutral sentiment data
            neutral_path = os.path.join(self.analysis_path, 'neutral')
            if os.path.exists(neutral_path):
                context['neutral'] = self._load_sentiment_data(neutral_path, 'neutral')
            
            # Load recommendations
            rec_path = os.path.join(self.analysis_path, 'recommendation', 'recommendation.json')
            if os.path.exists(rec_path):
                with open(rec_path, 'r', encoding='utf-8') as f:
                    context['recommendations'] = json.load(f)
            
            # Load sentiment trends
            trends_path = os.path.join(self.analysis_path, 'sentiment_trends.json')
            if os.path.exists(trends_path):
                with open(trends_path, 'r', encoding='utf-8') as f:
                    context['trends'] = json.load(f)
            
            # Load representative comments
            rep_path = os.path.join(self.analysis_path, 'representative_comments.json')
            if os.path.exists(rep_path):
                with open(rep_path, 'r', encoding='utf-8') as f:
                    context['representatives'] = json.load(f)
            
            logger.info(f"Loaded context with {len(context)} data sources")
            
        except Exception as e:
            logger.error(f"Error loading analysis context: {e}")
        
        return context
    
    def _load_sentiment_data(self, path: str, sentiment_type: str) -> Dict:
        """Load data for a specific sentiment type"""
        data = {}
        
        # Load summary
        summary_file = os.path.join(path, f'{sentiment_type}_summary.json')
        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                data['summary'] = json.load(f)
        
        # Load representatives
        rep_file = os.path.join(path, f'{sentiment_type}_representatives.json')
        if os.path.exists(rep_file):
            with open(rep_file, 'r', encoding='utf-8') as f:
                data['representatives'] = json.load(f)
        
        # Load top words
        words_file = os.path.join(path, f'{sentiment_type}_top_words.json')
        if os.path.exists(words_file):
            with open(words_file, 'r', encoding='utf-8') as f:
                data['top_words'] = json.load(f)
        
        return data
    
    def _build_context_prompt(self) -> str:
        """Build a concise context prompt from analysis data"""
        prompt_parts = []
        
        # Add statistics summary
        if self.context.get('trends'):
            trends = self.context['trends']
            summary = trends.get('summary', {})
            
            total_positive = summary.get('total_positive', trends.get('positive_count', 0))
            total_negative = summary.get('total_negative', trends.get('negative_count', 0))
            total_neutral = summary.get('total_neutral', trends.get('neutral_count', 0))
            total_reviews = summary.get('total_reviews', total_positive + total_negative + total_neutral)
            
            # Calculate percentages
            if total_reviews > 0:
                pos_pct = (total_positive / total_reviews) * 100
                neg_pct = (total_negative / total_reviews) * 100
                neu_pct = (total_neutral / total_reviews) * 100
            else:
                pos_pct = neg_pct = neu_pct = 0
            
            prompt_parts.append(f"""
SENTIMENT DISTRIBUTION:
- Positive: {total_positive} reviews ({pos_pct:.1f}%)
- Negative: {total_negative} reviews ({neg_pct:.1f}%)
- Neutral: {total_neutral} reviews ({neu_pct:.1f}%)
- Total Reviews: {total_reviews}
""")
        
        # Add summaries for each sentiment
        for sentiment_type in ['positive', 'negative', 'neutral']:
            sentiment_data = self.context.get(sentiment_type, {})
            if sentiment_data.get('summary'):
                summary_text = sentiment_data['summary'].get('summary', '')
                if summary_text:
                    prompt_parts.append(f"\n{sentiment_type.upper()} FEEDBACK SUMMARY:\n{summary_text}")
            
            # Add top keywords
            if sentiment_data.get('top_words'):
                words = sentiment_data['top_words'][:10]  # Top 10 words
                words_str = ', '.join([f"{w['word']} ({w['count']})" for w in words])
                prompt_parts.append(f"{sentiment_type.upper()} Keywords: {words_str}")
            
            # Add representative examples (limit to 3 per sentiment)
            if sentiment_data.get('representatives'):
                reps = sentiment_data['representatives'][:3]
                examples = [f"- \"{r.get('text', '')}\"" for r in reps]
                prompt_parts.append(f"\n{sentiment_type.upper()} Examples:\n" + "\n".join(examples))
        
        # Add recommendations
        if self.context.get('recommendations'):
            rec = self.context['recommendations'].get('recommendations', '')
            if rec:
                prompt_parts.append(f"\nRECOMMENDATIONS:\n{rec}")
        
        return "\n".join(prompt_parts)
    

    def ask_general(self, question: str) -> str:
        """
        Ask general questions without requiring analysis context.
        Handles:
        - Questions about Andrey Vlasenko (Andrey)
        - Questions about the platform/features
        - Form field explanations
        - Demo mode information
        
        Args:
            question: User's question in natural language
            
        Returns:
            AI-generated answer
        """
        try:
            # Route the question
            route = self._route_query(question)
            logger.info(f"General question routed to: {route}")
            
            if route == "Andrey_KB" and self.Andrey_index:
                # Andrey MODE: Answer about Andrey Vlasenko
                Andrey_context = self._retrieve_from_Andrey_kb(question, top_k=3)
                
                system_message = f"""You are an AI assistant for the LeadLink platform, authorized to provide information about Andrey Vlasenko, a Data Scientist and AI/ML engineer.

When asked "Who are you?", identify yourself as the AI assistant and then provide information about Andrey.

**IMPORTANT**: Answer in THIRD PERSON ("he", "his", "him") as an AI assistant representing Andrey Vlasenko.

Context from his professional knowledge base:
{Andrey_context}

Guidelines:
- Answer based ONLY on the context provided
- Use third person: "He worked at...", "His PhD was...", "He developed..."
- Be professional and informative, like an assistant presenting a Andrey
- If asked "Who are you?", respond: "I'm an AI assistant for the LeadLink platform. Let me tell you about Andrey Vlasenko: [then provide info]"
- If information is not in the context, say "I don't have that specific information in my knowledge base about Andrey"
- Keep answers concise but informative (2-4 sentences typically)
- Highlight his achievements and technical skills when relevant
- Start responses naturally: "Andrey is...", "He has...", "His experience includes..."

Answer the question based on the context:"""
                
            else:
                # PLATFORM MODE: General platform/form/demo questions
                platform_knowledge = """
# LeadLink Sentiment Analysis Platform

## Platform Overview
LeadLink is an AI-powered sentiment analysis platform that helps businesses understand customer feedback from social media and review sites.

## How It Works
1. **Data Collection**: Scrapes comments/reviews from Facebook, YouTube, TripAdvisor
2. **AI Analysis**: Uses DistilBERT model (fine-tuned transformer) to classify sentiment
3. **Classification**: Each comment is categorized as POSITIVE, NEGATIVE, or NEUTRAL
4. **Insights**: Generates summaries, trends, and actionable recommendations
5. **Video Generation**: Creates AI-generated advertisement videos using results

## Demo Mode
**Important**: This site runs in DEMO MODE to:
- Speed up analysis (limited comment crawling)
- Avoid CAPTCHA protections from websites
- Demonstrate capabilities without full-scale crawling

Note: Full RoBERTa model was successfully tested on YouTube and TripAdvisor sites. Demo mode uses smaller datasets to showcase functionality quickly.

## Form Fields Explained

### 1. **Firmenname** (Company Name)
- The name of your business or Facebook page
- Example: "Café Berlin", "Tech Solutions GmbH"
- Used to identify your brand in the analysis

### 2. **Facebook-Seite** (Facebook Page URL)
- Full URL to your Facebook page
- Example: https://www.facebook.com/YourBusinessName
- Platform will scrape comments from posts on this page

### 3. **Analysemethode** (Analysis Method)
- Choose how to collect data:
  - **Single Post**: Analyze one specific post (provide URL)
  - **Recent Posts**: Analyze last N posts from timeline
  - **Date Range**: Analyze posts within specific dates

### 4. **E-Mail für Berichtszustellung** (Report Delivery Email)
- Your email address to receive PDF reports
- Analysis results will be sent here
- Optional but recommended for record-keeping

### 5. **Sprache** (Language)
- Select language: German (DE) or English (EN)
- Affects report language and some processing

## Features (Buttons Explained)

### 🔄 **Weitere Analyse** (New Analysis)
- Start another sentiment analysis
- Resets form to analyze different page/company

### 🎬 **Video Script erstellen** (Generate Video Script)
- Creates AI-generated advertisement script based on sentiment results
- Uses Groq LLaMA 3.3 to write compelling ad copy
- Script is then converted to 30-second video

### 🎯 **Campaign Optimizer**
- Test multiple advertisement variants (English text recommended)
- Uses same DistilBERT model to predict audience reaction
- Shows which variant will generate most positive sentiment
- **Directly derived from sentiment analysis** - tests how customers will react

### 📊 **Live Monitor**
- Real-time dashboard of sentiment trends
- Shows positive/negative/neutral percentages
- Interactive charts and gauge visualization
- Displays representative comments for each sentiment

### 📥 **PDF Download**
- Download complete analysis report
- Includes all statistics, charts, and summaries
- Professional format for presentations/records

## AI Advertisement Film
The video shown on the homepage is **100% AI-generated**:
- **Script**: Written by LLaMA 3.3 AI model
- **Visuals**: Generated by Stable Diffusion image AI
- **Audio**: Text-to-speech synthesis
- **Purpose**: Demonstrate targeted advertisement creation based on sentiment data

Goal: Provide businesses with data-driven, personalized advertisements that resonate with their audience's feedback.

## Technical Stack
- **Sentiment Model**: DistilBERT (transformer-based, 66M parameters)
- **NLP**: Hugging Face transformers pipeline
- **Video AI**: Stable Diffusion for imagery
- **Script AI**: Groq LLaMA 3.3 (70B parameters)
- **Backend**: Python FastAPI + Docker
- **Frontend**: JavaScript + Chart.js
- **Deployment**: AWS EC2

## Privacy & Data
- Comments are analyzed in real-time, not stored permanently
- No personal data collection beyond email (optional)
- GDPR compliant processing
- Demo mode limits crawling to avoid platform rate limits
"""

                system_message = f"""You are an expert assistant for the LeadLink sentiment analysis platform.

You help users understand:
- How the platform works
- What form fields mean and how to fill them
- What each button/feature does
- Demo mode limitations and capabilities
- The AI-generated advertisement film

Platform Knowledge Base:
{platform_knowledge}

Guidelines:
- Provide clear, helpful explanations
- Be concise (2-4 sentences typically)
- Reference demo mode when discussing limitations
- Emphasize that Campaign Optimizer IS sentiment analysis
- Explain form fields in simple terms
- Mention the AI-generated nature of the advertisement film
- If question is about analysis results, politely say "Please run an analysis first, then I can answer questions about your specific results"

Answer the question based on the knowledge above:"""
            
            # Build messages list
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ]
            
            # Get response from Groq
            logger.info(f"Sending general question to Groq (route: {route})")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,  # Balanced temperature
                max_tokens=512,
                top_p=0.9
            )
            
            answer = response.choices[0].message.content
            logger.info(f"General question answered successfully")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in general chatbot: {e}")
            return f"I encountered an error answering your question. Please try rephrasing or ask something else."

    def ask(self, question: str, include_history: bool = True) -> str:
        """
        Ask a question - automatically routes to Andrey KB or platform context
        
        Args:
            question: User's question in natural language
            include_history: Whether to include conversation history
            
        Returns:
            AI-generated answer based on appropriate context
        """
        try:
            # Route the question
            route = self._route_query(question)
            logger.info(f"Question routed to: {route}")
            
            if route == "Andrey_KB" and self.Andrey_index:
                # Andrey MODE: Answer about Andrey Vlasenko
                Andrey_context = self._retrieve_from_Andrey_kb(question, top_k=3)
                
                system_message = f"""You are an AI assistant for the LeadLink platform, authorized to provide information about Andrey Vlasenko, a Data Scientist and AI/ML engineer.

When asked "Who are you?", identify yourself as the AI assistant and then provide information about Andrey.

**IMPORTANT**: Answer in THIRD PERSON ("he", "his", "him") as an AI assistant representing Andrey Vlasenko.

Context from his professional knowledge base:
{Andrey_context}

Guidelines:
- Answer based ONLY on the context provided
- Use third person: "He worked at...", "His PhD was...", "He developed..."
- Be professional and informative, like an assistant presenting a Andrey
- If asked "Who are you?", respond: "I'm an AI assistant for the LeadLink platform. Let me tell you about Andrey Vlasenko: [then provide info]"
- If information is not in the context, say "I don't have that specific information in my knowledge base about Andrey"
- Keep answers concise but informative (2-4 sentences typically)
- Highlight his achievements and technical skills when relevant
- Start responses naturally: "Andrey is...", "He has...", "His experience includes..."

Answer the question based on the context:"""
                
            else:
                # PLATFORM MODE: Answer about sentiment analysis
                context_prompt = self._build_context_prompt()
                
                system_message = f"""You are an expert sentiment analysis assistant for the LeadLink platform.
You help users understand their customer feedback data.

You have access to the following sentiment analysis results:

{context_prompt}

Guidelines:
- Provide clear, actionable insights
- Use specific data and examples from the analysis
- Be concise but thorough
- If data is missing, say so
- Suggest follow-up questions when appropriate
- Focus on actionable recommendations

Answer questions based ONLY on the data provided above."""
            
            # Build messages list
            messages = [{"role": "system", "content": system_message}]
            
            # Add conversation history if requested
            if include_history and self.conversation_history:
                messages.extend(self.conversation_history[-4:])  # Last 2 exchanges
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Get response from Groq
            logger.info(f"Sending question to Groq (route: {route})")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3 if route == "PLATFORM" else 0.7,  # Higher temp for Andrey questions
                max_tokens=1024,
                top_p=0.9
            )
            
            answer = response.choices[0].message.content
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            logger.info(f"Generated answer of length {len(answer)} from {route}")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"I apologize, but I encountered an error processing your question: {str(e)}"
    
    def get_suggested_questions(self) -> List[str]:
        """Get suggested questions based on available data - includes both platform and Andrey questions"""
        suggestions = []
        
        # Platform questions (sentiment analysis)
        if self.context.get('trends'):
            suggestions.extend([
                "What is the overall sentiment distribution?",
                "What are the main positive feedback themes?",
                "What are the key complaints from customers?"
            ])
        
        if self.context.get('recommendations'):
            suggestions.append("What recommendations do you have based on this data?")
        
        # Andrey questions (if KB available)
        if self.Andrey_index:
            suggestions.extend([
                "Tell me about Andrey's background",
                "What projects has Andrey worked on?",
                "What is Andrey's experience with AI/ML?"
            ])
        
        return suggestions[:6]  # Return max 6 suggestions
    
    def reset_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info(f"Conversation history reset for job {self.job_id}")
