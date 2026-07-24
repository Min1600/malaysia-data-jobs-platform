# Malaysia Data Jobs ETL Pipeline 

## Overview
This project demonstrates an ETL pipeline for collecting and processing data job listings in Kuala Lumpur, Malaysia using a medallion architecture

The pipeline collects listings from online job platforms, preserves raw data, transforms and standardizes records using SQL, and enriches unstructured job descriptions using an LLM.

The pipeline currently focuses on roles such as Data Analyst, Data Engineer, Data Scientist, and related positions.

## Architecture

### Data Sources
    - LinkedIn
    - Jobstreet
### Technology Stack
    - Python: Web scraping and pipeline orchestration
    - PostgreSQL: Data storage and SQL transformations
    - HuggingFace: Raw data storage
    - Streamlit: Pipeline interface and monitoring
    - GitHub Actions: Scheduled pipeline execution
    - Docker: PostgreSQL containerization

### ETL Pipeline

1. Extract Job listings are scraped from online job platforms on a scheduled basis.
2. Raw job data is loaded into a PostgreSQL Bronze layer as the single source of truth.
3. The Bronze data is transformed into a standardized Silver layer using SQL.
4. Unstructured job descriptions are processed using a Groq-hosted LLM to extract structured information
5. The Gold layer is planned as the final analytics-ready layer of the pipeline.

## Pipeline

### 1. Data Collection
### 2. Bronze Layer
### 3. Silver Layer
### 4. AI Enrichment
AI enrichment is stored separately from the Silver layer to preserve the distinction between deterministic transformations and probabilistic LLM-generated data. This also allows AI enrichment to be rerun independently without rebuilding the core job dataset.
### 5. Gold / Analytics Layer

## Data Model

## Technologies

## Project Structure

## Data Quality & Deduplication
The pipeline handles duplicate jobs at multiple stages.

### Bronze-level duplicates

Jobs are uniquely identified by:

(source, job_id)

This prevents the same listing from the same platform from being ingested multiple times.

### Cross-source duplicates

The same job may appear on multiple platforms with different IDs.

For example:

LinkedIn:
Data Analyst | Company A | Kuala Lumpur

JobStreet:
Data Analyst | Company A | Kuala Lumpur

These records are retained because they originate from different sources, but they can be flagged as potential cross-source duplicates during Silver-layer processing.

This preserves source-level lineage while allowing downstream analysis to identify potentially duplicated real-world job postings.

## AI Enrichment
Job descriptions are highly unstructured and inconsistent across job platforms. Important information such as technical skills and requirements may appear under different headings or may not be consistently extractable using traditional scraping techniques.

To address this, the pipeline uses an LLM to extract structured information from job descriptions.

The model receives a cleaned job description and returns a Pydantic-validated structure:

class JobRequirements(BaseModel):
    skills: list[str]
    requirements: list[str]

Example output:

```python
{

  "skills": [
    "SQL",
    "Python",
    "Power BI",
    "Tableau",
    "Excel"
  ],

  "requirements": [
    "0-1 year of experience in data analysis or a related field",
    "Foundational knowledge of SQL and Excel",
    "Strong communication skills",
    "Ability to prioritize and manage multiple tasks"
  ]
  
}
```

The enrichment results are stored separately from the core Silver dataset and linked through job_key.

This allows the AI enrichment process to be incremental. Jobs that have already been enriched do not need to be sent to the LLM again, reducing unnecessary API usage and processing costs.

## Challenges and design decisions
### Why PostgreSQL?

PostgreSQL was selected as the primary analytical database due to its support for relational modeling, JSONB data types, constraints, indexing, and SQL-based transformations.

### Why separate AI enrichment?

AI-generated data is stored separately from deterministic Silver transformations to allow independent reprocessing and model/prompt versioning.

### Why incremental processing?

Reprocessing previously enriched jobs would unnecessarily increase LLM API usage. The enrichment pipeline therefore checks for existing job_key records before sending new jobs for enrichment.

### Why keep Bronze data?

Raw data is preserved to maintain historical lineage and allow transformations to be revised without recollecting the source data.
## Running the Project

## Future Improvements