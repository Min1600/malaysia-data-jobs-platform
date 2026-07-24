# Malaysia data jobs platform

## Overview

## Architecture

## Data Sources

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