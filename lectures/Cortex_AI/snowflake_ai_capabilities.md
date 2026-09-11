# Snowflake AI Capabilities — Hands-On Tutorial

> **Prerequisites**: A Snowflake account with the `CORTEX_USER` database role or equivalent privileges.
> All queries run against the **BOOTCAMP.PUBLIC** schema, which is set up in Module 0 below.

---

## Table of Contents

1. [Module 0 — Environment Setup](#module-0--environment-setup)
2. [Module 1 — AI_COMPLETE: Text Generation with LLMs](#module-1--ai_complete-text-generation-with-llms)
3. [Module 2 — AI_SENTIMENT: Sentiment Analysis](#module-2--ai_sentiment-sentiment-analysis)
4. [Module 3 — AI_CLASSIFY: Text Classification](#module-3--ai_classify-text-classification)
5. [Module 4 — AI_EXTRACT: Structured Data Extraction](#module-4--ai_extract-structured-data-extraction)
6. [Module 5 — AI_TRANSLATE: Language Translation](#module-5--ai_translate-language-translation)
7. [Module 6 — AI_FILTER: Semantic Filtering](#module-6--ai_filter-semantic-filtering)
8. [Module 7 — AI_SUMMARIZE_AGG: Aggregated Summaries](#module-7--ai_summarize_agg-aggregated-summaries)
9. [Module 8 — AI_EMBED & AI_SIMILARITY: Embeddings and Semantic Search](#module-8--ai_embed--ai_similarity-embeddings-and-semantic-search)
10. [Module 9 — AI_COMPLETE: Structured Output (JSON)](#module-9--ai_complete-structured-output-json)
11. [Module 10 — Combining AI Functions in a Pipeline](#module-10--combining-ai-functions-in-a-pipeline)
12. [Module 11 — AI_COUNT_TOKENS: Cost Estimation](#module-11--ai_count_tokens-cost-estimation)
13. [Appendix — Cleanup](#appendix--cleanup)

---

## Module 0 — Environment Setup

This module creates the **BOOTCAMP** database and loads sample data that the rest of the
tutorial uses. Run these statements once before starting.

### 0.1 Create the database

```sql
CREATE DATABASE IF NOT EXISTS BOOTCAMP;
USE DATABASE BOOTCAMP;
USE SCHEMA PUBLIC;
```

### 0.2 Customer Reviews table

Realistic product reviews with star ratings — used for sentiment, classification, and
summarization exercises.

```sql
CREATE OR REPLACE TABLE CUSTOMER_REVIEWS (
    review_id    INT,
    customer_name VARCHAR,
    product      VARCHAR,
    review_text  VARCHAR,
    star_rating  INT,
    review_date  DATE
);

INSERT INTO CUSTOMER_REVIEWS VALUES
(1, 'Alice Chen',     'Wireless Headphones', 'These headphones are absolutely amazing! The noise cancellation is top-notch and battery life lasts all day. Best purchase I have made this year.', 5, '2025-01-15'),
(2, 'Bob Martinez',   'Wireless Headphones', 'Sound quality is decent but they hurt my ears after an hour. The Bluetooth connection drops occasionally. Not worth the premium price.', 2, '2025-01-18'),
(3, 'Carol Johnson',  'Smart Watch',         'Love the fitness tracking features! The heart rate monitor is accurate and the sleep tracking has helped me improve my habits. Highly recommend.', 5, '2025-02-01'),
(4, 'David Kim',      'Smart Watch',         'The watch face scratched within a week of normal use. Customer support was unhelpful and rude. Very disappointed with this purchase.', 1, '2025-02-10'),
(5, 'Eva Rossi',      'Laptop Stand',        'Good quality aluminum build. Improved my posture at work. Only complaint is the assembly instructions were confusing.', 4, '2025-02-15'),
(6, 'Frank Liu',      'Laptop Stand',        'Arrived broken. Requested a replacement but it took 3 weeks. The stand itself is fine once you get a working one.', 2, '2025-02-20'),
(7, 'Grace Okafor',   'Portable Charger',    'This portable charger is a lifesaver during travel! Charges my phone 3 times and fits in my pocket. Fast charging works great.', 5, '2025-03-01'),
(8, 'Henry Tanaka',   'Portable Charger',    'Stopped working after two months. The charging port became loose and now it wont charge at all. Waste of money.', 1, '2025-03-10'),
(9, 'Iris Patel',     'Ergonomic Keyboard',  'Took a week to get used to the split design, but now I can type faster with zero wrist pain. Worth every penny for anyone who types all day.', 5, '2025-03-15'),
(10,'Jake Thompson',  'Ergonomic Keyboard',  'The keys feel mushy and the wireless receiver has terrible range. Had to return it. My old keyboard was better in every way.', 1, '2025-03-20');
```

### 0.3 Support Tickets table

Customer support messages with varying urgency — used for classification, extraction,
and filtering exercises.

```sql
CREATE OR REPLACE TABLE SUPPORT_TICKETS (
    ticket_id     INT,
    customer_email VARCHAR,
    subject       VARCHAR,
    message       VARCHAR,
    priority      VARCHAR,
    created_at    TIMESTAMP
);

INSERT INTO SUPPORT_TICKETS VALUES
(101, 'alice@example.com', 'Cannot log in to my account',        'I have been trying to log in for the past 2 hours but keep getting an "invalid credentials" error. I have reset my password twice already. This is urgent as I need to access my files for a meeting in 30 minutes.', 'HIGH',   '2025-03-01 09:15:00'),
(102, 'bob@example.com',   'Feature request: dark mode',         'It would be great if you could add a dark mode option to the desktop application. Many of us work late at night and the bright white interface is hard on the eyes. Thanks for considering this!', 'LOW',    '2025-03-01 10:30:00'),
(103, 'carol@example.com', 'Billing discrepancy on my invoice',  'I was charged $49.99 this month but my plan is supposed to be $29.99/month. I did not authorize any upgrade. Please investigate and refund the difference immediately.', 'HIGH',   '2025-03-02 08:00:00'),
(104, 'david@example.com', 'App crashes when uploading files',   'Every time I try to upload a PDF larger than 10MB the app crashes completely. I have tried reinstalling and clearing the cache. Running on Windows 11 with 16GB RAM. This happens consistently.', 'MEDIUM', '2025-03-02 14:20:00'),
(105, 'eva@example.com',   'How to export data to CSV',          'Hi, I am new to the platform. Could someone walk me through how to export my dashboard data to a CSV file? I looked through the docs but could not find clear instructions.', 'LOW',    '2025-03-03 11:45:00'),
(106, 'frank@example.com', 'Data loss after system update',      'After your latest system update yesterday, all my saved reports from the last 3 months are gone. This is critical data that I need for quarterly reporting. Please restore my data immediately!', 'HIGH',   '2025-03-03 07:00:00'),
(107, 'grace@example.com', 'Integration with Slack not working',  'The Slack integration stopped sending notifications two days ago. I have re-authorized the connection and checked my webhook settings. Nothing seems to work. Our team relies on these alerts.', 'MEDIUM', '2025-03-04 09:30:00'),
(108, 'henry@example.com', 'Compliment for support team',         'Just wanted to say thank you to Sarah from your support team. She resolved my complex migration issue in under an hour. Exceptional service! You should give her a raise.', 'LOW',    '2025-03-04 16:00:00');
```

### 0.4 Multilingual Content table

Text in six languages — used for translation exercises.

```sql
CREATE OR REPLACE TABLE MULTILINGUAL_CONTENT (
    content_id     INT,
    language_code  VARCHAR(5),
    original_text  VARCHAR,
    source_context VARCHAR
);

INSERT INTO MULTILINGUAL_CONTENT VALUES
(1, 'es', 'El servicio al cliente fue excelente. Resolvieron mi problema en menos de cinco minutos. Estoy muy satisfecho con la experiencia.', 'Customer feedback - Spain'),
(2, 'fr', 'Je suis tres decu par la qualite du produit. Il est tombe en panne apres seulement deux semaines. Je demande un remboursement complet.', 'Customer feedback - France'),
(3, 'de', 'Die neue Software-Version hat viele nuetzliche Funktionen. Besonders die automatische Datensicherung ist sehr praktisch fuer unsere taegliche Arbeit.', 'Product review - Germany'),
(4, 'ja', 'このアプリケーションは使いやすくて、デザインも美しいです。毎日の業務効率が大幅に向上しました。', 'Product review - Japan'),
(5, 'pt', 'Precisamos de mais opcoes de personalizacao no painel de controle. A interface atual e muito limitada para as necessidades da nossa equipe.', 'Feature request - Brazil'),
(6, 'zh', '这个平台的数据分析功能非常强大。可视化报表帮助我们快速做出商业决策。', 'Product review - China');
```

### 0.5 Knowledge Base table

Short articles about Snowflake — used for embeddings and semantic search exercises.

```sql
CREATE OR REPLACE TABLE KNOWLEDGE_BASE (
    article_id INT,
    title      VARCHAR,
    category   VARCHAR,
    content    VARCHAR
);

INSERT INTO KNOWLEDGE_BASE VALUES
(1, 'Getting Started with Snowflake',    'Tutorial',        'Snowflake is a cloud-based data warehousing platform that allows you to store, process, and analyze large volumes of data. To get started, create an account, set up a warehouse, and load your data using the COPY INTO command or Snowpipe for continuous ingestion.'),
(2, 'Understanding Virtual Warehouses',  'Architecture',    'Virtual warehouses in Snowflake are clusters of compute resources that execute SQL queries and DML operations. They can be resized on the fly and suspended when not in use. Multi-cluster warehouses automatically scale out to handle concurrency.'),
(3, 'Data Sharing Best Practices',       'Best Practices',  'Snowflake Secure Data Sharing lets you share live data with other accounts without copying or moving it. Create shares, add databases, schemas, and tables, then grant access to consumer accounts. Data is always up to date because consumers access the provider account data directly.'),
(4, 'Time Travel and Fail-safe',         'Data Protection', 'Snowflake Time Travel allows you to access historical data at any point within the retention period, which can be up to 90 days for permanent tables. Fail-safe provides an additional 7 days of data recovery by Snowflake support for disaster recovery scenarios.'),
(5, 'Optimizing Query Performance',      'Performance',     'To optimize queries in Snowflake, use clustering keys on large tables, leverage result caching, right-size your warehouses, minimize data scanning with partition pruning, and use materialized views for expensive repeated computations.'),
(6, 'Introduction to Snowpark',          'Development',     'Snowpark enables developers to write data pipelines and applications in Python, Java, or Scala that run directly on Snowflake. It provides DataFrame-style APIs and supports user-defined functions (UDFs) for custom logic execution within the Snowflake engine.'),
(7, 'Cost Management Strategies',        'Administration',  'Control Snowflake costs by setting resource monitors, using auto-suspend and auto-resume on warehouses, right-sizing compute, leveraging caching, and monitoring usage with the ACCOUNT_USAGE schema. Consider serverless features to eliminate warehouse management overhead.'),
(8, 'Security and Governance Overview',  'Security',        'Snowflake provides enterprise-grade security including end-to-end encryption, role-based access control (RBAC), dynamic data masking, row access policies, column-level security, and network policies. Use the SECURITYADMIN role to manage access controls.');
```

### 0.6 Meeting Notes table

Unstructured business meeting notes — used for extraction and summarization exercises.

```sql
CREATE OR REPLACE TABLE MEETING_NOTES (
    note_id      INT,
    meeting_date DATE,
    raw_notes    VARCHAR
);

INSERT INTO MEETING_NOTES VALUES
(1, '2025-03-01', 'Q1 Planning meeting with Sarah Chen (VP Engineering) and Marco Rossi (Product Manager). Discussed launching the new analytics dashboard by April 15th 2025. Budget approved at $150,000. Action items: Sarah to finalize tech stack by March 10th, Marco to complete user research by March 15th. Risk: potential delay if third-party API vendor doesnt deliver on time.'),
(2, '2025-03-05', 'Customer success review with the Acme Corp account. Annual contract worth $2.4M is up for renewal in June. Customer satisfaction score dropped from 8.5 to 7.2. Main complaints: slow response times on support tickets and missing SSO integration. Jennifer Walsh (Account Manager) to schedule executive business review by March 20th. Escalation to VP Sales recommended.'),
(3, '2025-03-10', 'Sprint retrospective for Team Alpha. Velocity improved from 45 to 62 story points. Completed migration of payment service to microservices architecture. Three production incidents last sprint, all resolved within SLA. Team morale is high but concerns about upcoming deadline for GDPR compliance feature due May 1st. Need to hire 2 additional backend engineers.'),
(4, '2025-03-15', 'Board of Directors quarterly update presented by CEO Amanda Foster. Revenue grew 23% year-over-year to $45M in Q1. Customer base expanded to 1,200 enterprise clients. New partnership with Azure announced for co-selling initiative. Headcount increased from 340 to 410 employees. IPO timeline discussed for Q3 2026. Board approved $5M investment in AI/ML capabilities.');
```

---

## Module 1 — AI_COMPLETE: Text Generation with LLMs

`AI_COMPLETE` is the most versatile Cortex AI function. It sends a prompt to an LLM and
returns the generated response. You can choose from multiple models depending on your
cost/quality tradeoff.

### 1.1 Simple text generation

```sql
-- Ask a question using a small, fast model
SELECT AI_COMPLETE(
    'llama3.1-8b',
    'Explain what a data warehouse is in exactly three sentences.'
) AS explanation;
```

### 1.2 Compare models on the same prompt

Run the same prompt against different models to see how quality and style differ.

```sql
SELECT
    'llama3.1-8b'       AS model, AI_COMPLETE('llama3.1-8b',       'What are the top 3 benefits of cloud data warehousing? Be concise.') AS response
UNION ALL
SELECT
    'llama3.3-70b'      AS model, AI_COMPLETE('llama3.3-70b',      'What are the top 3 benefits of cloud data warehousing? Be concise.') AS response
UNION ALL
SELECT
    'claude-haiku-4-5'  AS model, AI_COMPLETE('claude-haiku-4-5',  'What are the top 3 benefits of cloud data warehousing? Be concise.') AS response;
```

### 1.3 Using system and user messages (chat-style)

For more control, pass a structured message array with system and user roles.

```sql
SELECT AI_COMPLETE(
    'claude-haiku-4-5',
    [
        {'role': 'system', 'content': 'You are a concise SQL tutor. Answer in 2-3 sentences.'},
        {'role': 'user',   'content': 'What is the difference between WHERE and HAVING in SQL?'}
    ]
) AS response;
```

### 1.4 Using AI_COMPLETE on table data

Generate a one-line summary for each customer review.

```sql
SELECT
    review_id,
    customer_name,
    product,
    AI_COMPLETE(
        'claude-haiku-4-5',
        'Summarize this customer review in one sentence: ' || review_text
    ) AS ai_summary
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
LIMIT 5;
```

**Key takeaway**: `AI_COMPLETE` is the general-purpose workhorse. Use smaller models
(`llama3.1-8b`, `mistral-7b`) for high-throughput, low-cost tasks and larger models
(`claude-sonnet-4-6`, `llama3.3-70b`) when reasoning quality matters.

---

## Module 2 — AI_SENTIMENT: Sentiment Analysis

`AI_SENTIMENT` returns a score between **-1** (very negative) and **+1** (very positive)
for any text input. No model selection required — it uses a Snowflake-managed model.

### 2.1 Analyze individual text

```sql
SELECT
    AI_SENTIMENT('This product is absolutely incredible, I love it!') AS positive_example,
    AI_SENTIMENT('This is the worst experience I have ever had.')     AS negative_example,
    AI_SENTIMENT('The package arrived on Tuesday.')                   AS neutral_example;
```

### 2.2 Score all customer reviews

```sql
SELECT
    review_id,
    customer_name,
    product,
    star_rating,
    AI_SENTIMENT(review_text) AS sentiment_score,
    CASE
        WHEN AI_SENTIMENT(review_text) >  0.3 THEN 'Positive'
        WHEN AI_SENTIMENT(review_text) < -0.3 THEN 'Negative'
        ELSE 'Neutral'
    END AS sentiment_label
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
ORDER BY sentiment_score DESC;
```

### 2.3 Find mismatches between star ratings and sentiment

Sometimes customers leave positive text with low stars or negative text with high
stars. AI_SENTIMENT can surface these anomalies.

```sql
SELECT
    review_id,
    customer_name,
    star_rating,
    ROUND(AI_SENTIMENT(review_text), 3)  AS sentiment_score,
    review_text
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
WHERE
    (star_rating >= 4 AND AI_SENTIMENT(review_text) < 0)
    OR (star_rating <= 2 AND AI_SENTIMENT(review_text) > 0.3)
ORDER BY review_id;
```

**Key takeaway**: `AI_SENTIMENT` is lightweight and deterministic — great for scoring
large datasets without needing to write prompts or pick models.

---

## Module 3 — AI_CLASSIFY: Text Classification

`AI_CLASSIFY` assigns one of your provided category labels to a piece of text. The model
decides which label is the best semantic match — no training data required.

### 3.1 Classify a single text

```sql
SELECT AI_CLASSIFY(
    'My laptop screen is flickering and sometimes goes completely black',
    ['Hardware Issue', 'Software Bug', 'Account Problem', 'Feature Request', 'General Inquiry']
) AS category;
```

### 3.2 Classify support tickets into categories

```sql
SELECT
    ticket_id,
    subject,
    AI_CLASSIFY(
        message,
        ['Bug Report', 'Billing Issue', 'Feature Request', 'Account Access', 'General Question', 'Compliment', 'Data Issue']
    ) AS ai_category,
    priority
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
ORDER BY ticket_id;
```

### 3.3 Classify reviews by product aspect

Identify what aspect of the product the customer is talking about.

```sql
SELECT
    review_id,
    product,
    AI_CLASSIFY(
        review_text,
        ['Product Quality', 'Customer Service', 'Value for Money', 'Ease of Use', 'Durability', 'Shipping & Delivery']
    ) AS aspect,
    star_rating
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
ORDER BY product, review_id;
```

**Key takeaway**: `AI_CLASSIFY` is zero-shot — just provide the categories you care about
and it picks the best match. No training, no model selection, no prompt engineering.

---

## Module 4 — AI_EXTRACT: Structured Data Extraction

`AI_EXTRACT` pulls structured fields from unstructured text and returns them as a JSON
object. You define the fields you want and the model extracts them.

### 4.1 Extract fields from a single text

```sql
SELECT AI_EXTRACT(
    'Please contact John Smith at john.smith@acme.com or call 555-0123. He is the CTO at Acme Corporation based in San Francisco.',
    ['person_name', 'email', 'phone', 'job_title', 'company', 'city']
) AS extracted;
```

### 4.2 Extract action items from meeting notes

```sql
SELECT
    note_id,
    meeting_date,
    AI_EXTRACT(
        raw_notes,
        ['attendees', 'key_decisions', 'action_items', 'deadlines', 'budget', 'risks']
    ) AS extracted_data
FROM BOOTCAMP.PUBLIC.MEETING_NOTES
ORDER BY note_id;
```

### 4.3 Parse extracted JSON into columns

Use Snowflake's JSON operators to flatten the extracted output into relational columns.

```sql
SELECT
    note_id,
    meeting_date,
    e.value:"attendees"::VARCHAR      AS attendees,
    e.value:"key_decisions"::VARCHAR  AS key_decisions,
    e.value:"action_items"::VARCHAR   AS action_items,
    e.value:"deadlines"::VARCHAR      AS deadlines,
    e.value:"budget"::VARCHAR         AS budget,
    e.value:"risks"::VARCHAR          AS risks
FROM BOOTCAMP.PUBLIC.MEETING_NOTES,
     TABLE(FLATTEN(INPUT => ARRAY_CONSTRUCT(
         AI_EXTRACT(raw_notes, ['attendees','key_decisions','action_items','deadlines','budget','risks'])
     ))) e
ORDER BY note_id;
```

### 4.4 Extract support ticket metadata

```sql
SELECT
    ticket_id,
    subject,
    AI_EXTRACT(
        message,
        ['issue_type', 'affected_feature', 'steps_to_reproduce', 'urgency_level', 'customer_action_taken']
    ) AS ticket_metadata
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
ORDER BY ticket_id;
```

**Key takeaway**: `AI_EXTRACT` transforms unstructured text into structured JSON, making
it easy to build analytics on top of free-text data. Combine with Snowflake's native JSON
functions to create fully relational output.

---

## Module 5 — AI_TRANSLATE: Language Translation

`AI_TRANSLATE` translates text between languages. Specify the source language (or use
`''` for auto-detection) and the target language.

### 5.1 Simple translation

```sql
SELECT AI_TRANSLATE(
    'Snowflake provides a powerful cloud data platform.',
    'en',
    'es'
) AS spanish_translation;
```

### 5.2 Translate multilingual content to English

```sql
SELECT
    content_id,
    language_code,
    source_context,
    original_text,
    AI_TRANSLATE(original_text, language_code, 'en') AS english_translation
FROM BOOTCAMP.PUBLIC.MULTILINGUAL_CONTENT
ORDER BY content_id;
```

### 5.3 Auto-detect source language and translate

Use an empty string for the source language to let the model detect it automatically.

```sql
SELECT
    content_id,
    original_text,
    AI_TRANSLATE(original_text, '', 'en') AS english_translation
FROM BOOTCAMP.PUBLIC.MULTILINGUAL_CONTENT
ORDER BY content_id;
```

### 5.4 Translate and analyze sentiment in one query

Combine translation with sentiment analysis for a multilingual analytics pipeline.

```sql
SELECT
    content_id,
    language_code,
    source_context,
    AI_TRANSLATE(original_text, language_code, 'en')              AS english_text,
    ROUND(AI_SENTIMENT(AI_TRANSLATE(original_text, language_code, 'en')), 3) AS sentiment
FROM BOOTCAMP.PUBLIC.MULTILINGUAL_CONTENT
ORDER BY sentiment DESC;
```

**Key takeaway**: `AI_TRANSLATE` unlocks global data. Combine it with other AI functions
to build multilingual analytics pipelines without leaving SQL.

---

## Module 6 — AI_FILTER: Semantic Filtering

`AI_FILTER` returns `TRUE` or `FALSE` based on whether text matches a natural-language
condition. Think of it as a semantic WHERE clause.

### 6.1 Filter by semantic condition

```sql
SELECT
    review_id,
    customer_name,
    product,
    review_text
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
WHERE AI_FILTER(
    review_text,
    'The customer mentions a physical defect or hardware problem with the product'
)
ORDER BY review_id;
```

### 6.2 Find urgent support tickets

```sql
SELECT
    ticket_id,
    subject,
    message
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
WHERE AI_FILTER(
    message,
    'The customer is experiencing data loss or cannot access critical information'
)
ORDER BY ticket_id;
```

### 6.3 Identify reviews mentioning customer service

```sql
SELECT
    review_id,
    customer_name,
    review_text,
    star_rating
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
WHERE AI_FILTER(
    review_text,
    'The review mentions an experience with customer service or support staff'
)
ORDER BY review_id;
```

**Key takeaway**: `AI_FILTER` replaces brittle keyword matching with semantic
understanding. The condition is written in plain English, so it catches paraphrases,
synonyms, and implied meaning that `LIKE` or `REGEXP` would miss.

---

## Module 7 — AI_SUMMARIZE_AGG: Aggregated Summaries

`AI_SUMMARIZE_AGG` summarizes a group of text values into a single summary. Use it with
`GROUP BY` to create per-group summaries across a column of text.

### 7.1 Summarize all reviews for each product

```sql
SELECT
    product,
    COUNT(*) AS review_count,
    AI_SUMMARIZE_AGG(review_text) AS product_summary
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
GROUP BY product
ORDER BY product;
```

### 7.2 Summarize support tickets by priority

```sql
SELECT
    priority,
    COUNT(*) AS ticket_count,
    AI_SUMMARIZE_AGG(message) AS priority_summary
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
GROUP BY priority
ORDER BY
    CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END;
```

### 7.3 Summarize meeting notes for a date range

```sql
SELECT
    AI_SUMMARIZE_AGG(raw_notes) AS monthly_summary
FROM BOOTCAMP.PUBLIC.MEETING_NOTES
WHERE meeting_date BETWEEN '2025-03-01' AND '2025-03-31';
```

**Key takeaway**: `AI_SUMMARIZE_AGG` is an aggregate function like `SUM` or `AVG` — it
compresses many rows of text into a single, cohesive summary. Pair it with `GROUP BY`
for per-group executive summaries.

---

## Module 8 — AI_EMBED & AI_SIMILARITY: Embeddings and Semantic Search

`AI_EMBED` converts text into a vector (embedding) that captures its semantic meaning.
`AI_SIMILARITY` compares two pieces of text (or embeddings) and returns a similarity
score from 0 to 1.

### 8.1 Generate an embedding

```sql
SELECT AI_EMBED(
    'snowflake-arctic-embed-m',
    'How do I optimize query performance in Snowflake?'
) AS query_embedding;
```

### 8.2 Semantic search over the knowledge base

Find the articles most relevant to a user question — no keyword matching needed.

```sql
SET search_query = 'How can I reduce my Snowflake bill?';

SELECT
    article_id,
    title,
    category,
    ROUND(AI_SIMILARITY(
        'snowflake-arctic-embed-m',
        content,
        $search_query
    ), 4) AS relevance_score,
    content
FROM BOOTCAMP.PUBLIC.KNOWLEDGE_BASE
ORDER BY relevance_score DESC
LIMIT 5;
```

### 8.3 Find similar articles to a given article

```sql
SELECT
    a.article_id AS source_id,
    a.title      AS source_title,
    b.article_id AS similar_id,
    b.title      AS similar_title,
    ROUND(AI_SIMILARITY(
        'snowflake-arctic-embed-m',
        a.content,
        b.content
    ), 4) AS similarity
FROM BOOTCAMP.PUBLIC.KNOWLEDGE_BASE a
CROSS JOIN BOOTCAMP.PUBLIC.KNOWLEDGE_BASE b
WHERE a.article_id = 1 AND b.article_id != 1
ORDER BY similarity DESC;
```

### 8.4 Pre-compute embeddings for faster search

For production workloads, store embeddings in a column to avoid recomputing them.

```sql
CREATE OR REPLACE TABLE BOOTCAMP.PUBLIC.KNOWLEDGE_BASE_EMBEDDED AS
SELECT
    *,
    AI_EMBED('snowflake-arctic-embed-m', content) AS content_embedding
FROM BOOTCAMP.PUBLIC.KNOWLEDGE_BASE;

-- Now search using the pre-computed embeddings
SELECT
    title,
    category,
    ROUND(VECTOR_COSINE_SIMILARITY(
        content_embedding,
        AI_EMBED('snowflake-arctic-embed-m', 'How do I share data with another Snowflake account?')
    ), 4) AS relevance
FROM BOOTCAMP.PUBLIC.KNOWLEDGE_BASE_EMBEDDED
ORDER BY relevance DESC
LIMIT 3;
```

**Key takeaway**: Embeddings and similarity search let you build semantic search,
recommendation engines, and RAG (retrieval-augmented generation) pipelines entirely
within Snowflake SQL.

---

## Module 9 — AI_COMPLETE: Structured Output (JSON)

`AI_COMPLETE` can return structured JSON by using a system prompt that specifies the
output format. This is useful when you need machine-readable output.

### 9.1 Generate structured analysis of reviews

```sql
SELECT
    review_id,
    product,
    AI_COMPLETE(
        'claude-haiku-4-5',
        [
            {
                'role': 'system',
                'content': 'You are a review analyst. For each review, return ONLY a valid JSON object with these fields: {"sentiment": "positive|negative|mixed", "key_topics": ["topic1", "topic2"], "recommendation": "buy|avoid|conditional", "confidence": 0.0-1.0}. No other text.'
            },
            {
                'role': 'user',
                'content': review_text
            }
        ]
    ) AS structured_analysis
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
ORDER BY review_id;
```

### 9.2 Generate structured ticket triage

```sql
SELECT
    ticket_id,
    subject,
    AI_COMPLETE(
        'claude-haiku-4-5',
        [
            {
                'role': 'system',
                'content': 'You are a support ticket triage system. For each ticket, return ONLY a valid JSON object: {"department": "engineering|billing|support|product|general", "severity": "critical|high|medium|low", "estimated_resolution_hours": number, "requires_escalation": boolean, "suggested_response_template": "brief template"}. No other text.'
            },
            {
                'role': 'user',
                'content': message
            }
        ]
    ) AS triage_output
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
ORDER BY ticket_id;
```

### 9.3 Parse the JSON output into relational columns

```sql
SELECT
    ticket_id,
    subject,
    TRY_PARSE_JSON(
        AI_COMPLETE(
            'claude-haiku-4-5',
            [
                {
                    'role': 'system',
                    'content': 'Return ONLY a JSON object: {"department": "engineering|billing|support|product|general", "severity": "critical|high|medium|low", "requires_escalation": true/false}. No other text.'
                },
                {'role': 'user', 'content': message}
            ]
        )
    ) AS parsed,
    parsed:"department"::VARCHAR       AS department,
    parsed:"severity"::VARCHAR         AS severity,
    parsed:"requires_escalation"::BOOLEAN AS needs_escalation
FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS
ORDER BY ticket_id;
```

**Key takeaway**: By prompting `AI_COMPLETE` to return JSON, you bridge the gap between
unstructured LLM output and structured relational analytics. Use `TRY_PARSE_JSON` to
safely parse the output into queryable columns.

---

## Module 10 — Combining AI Functions in a Pipeline

The real power comes from composing multiple AI functions in a single query. Here is a
customer intelligence pipeline that analyzes reviews end-to-end.

### 10.1 Full review intelligence pipeline

```sql
SELECT
    r.review_id,
    r.customer_name,
    r.product,
    r.star_rating,

    -- Sentiment score
    ROUND(AI_SENTIMENT(r.review_text), 3) AS sentiment_score,

    -- Classification: what aspect is the review about?
    AI_CLASSIFY(
        r.review_text,
        ['Product Quality', 'Customer Service', 'Value for Money', 'Ease of Use', 'Durability']
    ) AS review_aspect,

    -- Extraction: pull out specific complaints or praises
    AI_EXTRACT(
        r.review_text,
        ['main_opinion', 'specific_feature_mentioned', 'improvement_suggestion']
    ) AS extracted_insights,

    -- AI-generated one-line summary
    AI_COMPLETE(
        'claude-haiku-4-5',
        'Summarize this review in exactly one sentence (max 15 words): ' || r.review_text
    ) AS one_liner

FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS r
ORDER BY r.review_id;
```

### 10.2 Support ticket routing pipeline

```sql
SELECT
    t.ticket_id,
    t.subject,
    t.priority,

    -- Classify the ticket type
    AI_CLASSIFY(
        t.message,
        ['Bug Report', 'Billing Issue', 'Feature Request', 'Account Access', 'Data Loss', 'Integration Issue', 'Compliment']
    ) AS ticket_type,

    -- Sentiment of the customer
    ROUND(AI_SENTIMENT(t.message), 3) AS customer_mood,

    -- Is this customer at risk of churning?
    AI_FILTER(
        t.message,
        'The customer is frustrated, threatening to leave, or demanding a refund'
    ) AS churn_risk,

    -- Extract key details
    AI_EXTRACT(
        t.message,
        ['affected_product_area', 'customer_request', 'workaround_attempted']
    ) AS key_details

FROM BOOTCAMP.PUBLIC.SUPPORT_TICKETS t
ORDER BY t.ticket_id;
```

**Key takeaway**: Snowflake AI functions compose naturally in SQL. You can build rich
analytics pipelines that classify, score, extract, filter, and summarize — all in a
single query with no external APIs or infrastructure.

---

## Module 11 — AI_COUNT_TOKENS: Cost Estimation

`AI_COUNT_TOKENS` tells you how many tokens a string consumes for a given model. Use it
to estimate costs before running expensive queries at scale.

### 11.1 Count tokens for a single string

```sql
SELECT AI_COUNT_TOKENS('llama3.1-8b', 'Hello, how are you today?') AS token_count;
```

### 11.2 Estimate token usage across your table

```sql
SELECT
    review_id,
    LENGTH(review_text) AS char_count,
    AI_COUNT_TOKENS('claude-haiku-4-5', review_text) AS token_count
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS
ORDER BY token_count DESC;
```

### 11.3 Estimate total tokens for a batch job

```sql
SELECT
    COUNT(*) AS total_rows,
    SUM(AI_COUNT_TOKENS('claude-haiku-4-5', review_text)) AS total_input_tokens,
    ROUND(total_input_tokens / 1000, 2) AS thousands_of_tokens
FROM BOOTCAMP.PUBLIC.CUSTOMER_REVIEWS;
```

**Key takeaway**: Always estimate token counts before running AI functions on large
tables. This helps you predict credit consumption and choose the right model for your
budget.

---

## Appendix — Cleanup

When you are done with the tutorial, drop the database to remove all objects.

```sql
-- WARNING: This drops everything created in this tutorial
DROP DATABASE IF EXISTS BOOTCAMP;
```

---

## Quick Reference: Snowflake AI Functions

| Function | Purpose | Input | Output |
|---|---|---|---|
| `AI_COMPLETE` | General-purpose text generation | Text + model name | Generated text |
| `AI_SENTIMENT` | Sentiment scoring | Text | Float (-1 to +1) |
| `AI_CLASSIFY` | Zero-shot classification | Text + category array | Best-matching category |
| `AI_EXTRACT` | Structured field extraction | Text + field name array | JSON object |
| `AI_TRANSLATE` | Language translation | Text + source lang + target lang | Translated text |
| `AI_FILTER` | Semantic true/false filtering | Text + condition string | Boolean |
| `AI_SUMMARIZE_AGG` | Aggregate summarization | Column of text (GROUP BY) | Summary string |
| `AI_EMBED` | Generate vector embedding | Model + text | Vector |
| `AI_SIMILARITY` | Compare text similarity | Model + two texts | Float (0 to 1) |
| `AI_COUNT_TOKENS` | Token counting | Model + text | Integer |

---

*Tutorial created for the BOOTCAMP database. All queries are self-contained and
executable in order.*
