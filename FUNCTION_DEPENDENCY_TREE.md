# Function Dependency Tree - LeadLink Sentiment Analysis Platform

## Main API Pipeline (`main_api.py`)

```
run_analysis_pipeline()
│
├── cleanup_old_jobs()                                    [cleanup_old_jobs.py]
├── initialize_mlflow_tracking()                          [pipeline_helpers.py]
├── setup_analysis_directories()                          [pipeline_helpers.py]
├── prepare_html_content()                                [pipeline_helpers.py]
│   ├── download_page_fun()                              [download_page_fun.py]
│   │   ├── download_with_selenium()
│   │   └── download_with_requests()
│   └── process_search_method()                          [search_methods_fun.py]
│       ├── Google_Search()
│       └── Multiple_URLs()
│
├── execute_sentiment_analysis()                          [pipeline_helpers.py]
│   ├── extract_text_fun()                               [extract_text_fun.py]
│   │   ├── extract_text_blocks()
│   │   ├── clean_text()
│   │   ├── save_text_blocks()
│   │   └── split_by_separators()
│   │
│   ├── Context_analyzer_RoBERTa_fun()                   [Context_analyzer_RoBERTa_fun.py]
│   │   ├── load_combined_dataset()
│   │   ├── analyze_sentiment_enhanced()
│   │   │   └── compute_original_score()
│   │   ├── normalize_scores_by_sentiment()
│   │   └── track_sentiment_run()                       [mlflow_tracking.py]
│   │
│   ├── vizualization()                                  [vizualization.py]
│   │   ├── read_extracted_text_files()
│   │   ├── create_text_vectors()
│   │   └── find_representative_comments()
│   │
│   └── summarize_sentiments_fun()                      [summarize_sentiments_fun.py]
│       ├── read_representatives_json()
│       ├── create_summary_prompt()
│       ├── query_groq_api()
│       ├── save_summary()
│       ├── has_duplicate_sentence()
│       └── is_quoted_or_citation()
│
├── generate_ai_summaries()                              [pipeline_helpers.py]
│   ├── summarize_sentiments_fun()                      [see above]
│   └── recommendation_fun()                            [recommendation_fun.py]
│       ├── read_summary_file()
│       ├── create_recommendation_prompt()
│       ├── query_groq_api()
│       └── save_recommendation()
│
├── calculate_and_save_insurance_risk()                  [pipeline_helpers.py]
│   └── calculate_insurance_risk()                      [insurance_calculator.py]
│       ├── _calculate_risk_score()
│       ├── _determine_risk_level()
│       ├── _analyze_trend_risk()
│       └── _get_trend_status()
│
├── generate_and_copy_pdf()                              [pipeline_helpers.py]
│   └── generate_pdf_fun()                              [pdf_generation/generate_pdf_fun.py]
│       ├── load_company_name()                         [pdf_generation/pdf_styles.py]
│       └── draw_header_stripe()                        [pdf_generation/pdf_header.py]
│
├── finalize_job_success()                               [pipeline_helpers.py]
│   └── send_report_email_fun()                         [send_report_email_fun.py]
│       └── send_email()                                [send_email.py]
│           ├── create_email_message()
│           └── attach_pdf_report()
│
└── handle_job_failure()                                 [pipeline_helpers.py]
```

## RAG Chatbot System (`chatbot_analyzer.py`)

```
ResultsChatbot class
│
├── __init__()
│   ├── SentenceTransformer('paraphrase-MiniLM-L6-v2')
│   ├── _initialize_candidate_kb()
│   │   └── FAISS.from_texts()
│   └── _initialize_results_index()
│
├── query()
│   ├── _route_to_knowledge_base()
│   ├── _retrieve_from_candidate_kb()
│   │   └── candidate_index.similarity_search()
│   ├── _retrieve_from_results()
│   │   └── results_index.similarity_search()
│   └── _generate_response()
│       └── query_groq_api()
│
└── _extract_sentiment_data()
```

## Auxiliary Functions

### Campaign Predictor (`campaign_predictor.py`)
```
predict_campaign_variants()
├── load_existing_data()
├── extract_date_from_text()
└── query_groq_api()
```

### Video Script Generator (`video_script_generator.py`)
```
generate_video_script()
├── read_summary_file()
├── query_groq_api()
└── process_sentiment_summary()
```

### Dashboard Data (`dashboard_data.py`)
```
get_dashboard_data()
├── extract_source_info_from_db()
├── load_existing_data()
└── export_dashboard_csv()
```

## Configuration Loading (`config/config.py`)

```
load_all_configs()
├── load_configurations()
├── extract_email_config()
└── extract_groq_config()
```

## Key Data Flow

1. **User Request** → `run_analysis_pipeline()`
2. **Download/Search** → `prepare_html_content()` → `download_page_fun()` or `process_search_method()`
3. **Text Extraction** → `extract_text_fun()` → Individual review text files
4. **Sentiment Analysis** → `Context_analyzer_RoBERTa_fun()` → JSON with scores
5. **Visualization** → `vizualization()` → Representative comments selection
6. **AI Summaries** → `summarize_sentiments_fun()` → Groq API → Summary text
7. **Recommendations** → `recommendation_fun()` → Groq API → Action items
8. **Risk Calculation** → `calculate_insurance_risk()` → Risk metrics JSON
9. **PDF Generation** → `generate_pdf_fun()` → Branded PDF report
10. **Email Delivery** → `send_report_email_fun()` → SMTP email with attachment
11. **Chatbot Queries** → `ResultsChatbot.query()` → FAISS retrieval → Groq API → Response

## External Dependencies

- **HuggingFace Transformers**: DistilBERT model for sentiment classification
- **Sentence Transformers**: paraphrase-MiniLM-L6-v2 for embeddings
- **FAISS**: Vector similarity search for RAG
- **Groq API**: LLM for summaries, recommendations, chatbot responses
- **MLflow**: Experiment tracking and logging
- **ReportLab**: PDF generation
- **SMTP**: Email delivery
- **Selenium/Requests**: Web scraping

## Critical Paths

### Fast Path (Cached)
```
run_analysis_pipeline → prepare_html_content (cache hit) → execute_sentiment_analysis → PDF → Email
Time: ~30 seconds
```

### Full Path (New URL)
```
run_analysis_pipeline → download_page_fun (Selenium) → extract_text_fun → 
Context_analyzer_RoBERTa_fun (ML inference) → vizualization → summarize_sentiments_fun (Groq) → 
recommendation_fun (Groq) → calculate_insurance_risk → generate_pdf_fun → send_report_email_fun
Time: 2-5 minutes
```

### Chatbot Path
```
User question → ResultsChatbot.query → route_to_knowledge_base → 
FAISS similarity_search → retrieve context → Groq API → response
Time: 1-3 seconds
```
