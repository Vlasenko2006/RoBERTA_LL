# Top-Level Architecture

## Request Flow

```
┌─────────────┐
│ index.html  │  User fills form (company, email, URL)
│ (port 3001) │  JavaScript: fetch('/api/analyze', {POST})
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   NGINX     │  Proxies /api/* → python-service:8001
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  main_api.py (FastAPI on port 8001)                  │
│                                                       │
│  STARTUP: CONFIG = load_all_configs()                │
│           ├─► config/config.yaml      [ML params]    │
│           ├─► config/config_names.yaml [Branding]    │
│           └─► config/config_key.yaml   [API keys]    │
│                                                       │
│  ENDPOINTS:                                           │
│  POST /api/analyze          → run_analysis_pipeline()│
│  GET  /api/dashboard        → get_dashboard_data()   │
│  POST /api/predict-campaign → predict_campaign_variants()
│  POST /api/generate-video   → generate_video_script()│
│  POST /api/chatbot          → chatbot.query()        │
└──────┬───────────────┬───────────────┬───────────────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ dashboard_  │ │ campaign_    │ │ video_script_   │
│ data.py     │ │ predictor.py │ │ generator.py    │
│             │ │              │ │                 │
│ Reads:      │ │ Reads:       │ │ Reads:          │
│ my_volume/  │ │ sentiment    │ │ summary.txt     │
│ *.db, JSON  │ │ data         │ │                 │
│             │ │              │ │                 │
│ Returns:    │ │ Calls:       │ │ Calls:          │
│ Dashboard   │ │ query_groq   │ │ query_groq_api()│
│ metrics     │ │ _api()       │ │                 │
└─────────────┘ └──────┬───────┘ └────────┬────────┘
                       │                  │
                       └────────┬─────────┘
                                ▼
                       ┌─────────────────┐
                       │  Groq API       │
                       │  (Llama 3.1)    │
                       └─────────────────┘
```

## Main Pipeline: run_analysis_pipeline()

```
1. Download page         → cache/
2. Extract text          → my_volume/{job_id}/extracted_text/
3. Analyze sentiment     → my_volume/{job_id}/analysis_results.json
4. Generate summaries    → my_volume/{job_id}/summary.txt (Groq)
5. Generate recommendations → my_volume/{job_id}/recommendations.txt (Groq)
6. Calculate risk        → my_volume/{job_id}/insurance_risk.json
7. Generate PDF          → my_volume/{job_id}/report.pdf
8. Send email            → SMTP with PDF attachment
```

## Configuration Loading

```python
load_all_configs()
├─► config/config.yaml         # ML: model_name, cache_dir, thresholds
├─► config/config_names.yaml   # Branding: colors, company name
└─► config/config_key.yaml     # Secrets: groq.api_key, email.smtp
```

## Key Functions

| Endpoint | Function | What It Does |
|----------|----------|--------------|
| `/api/analyze` | `run_analysis_pipeline()` | Full 8-step sentiment analysis |
| `/api/dashboard` | `get_dashboard_data()` | Aggregate metrics from all jobs |
| `/api/predict-campaign` | `predict_campaign_variants()` | LLM suggests 3 campaign strategies |
| `/api/generate-video` | `generate_video_script()` | LLM creates 60-sec video script |
| `/api/chatbot` | `chatbot.query()` | RAG over results + FAISS |

## Timing

- **Cached URL**: 30 seconds
- **New URL**: 2-5 minutes  
- **Chatbot**: 1-3 seconds
