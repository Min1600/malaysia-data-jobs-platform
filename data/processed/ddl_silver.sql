/*
===============================================================================
DDL Script: Create Silver Table
===============================================================================
Script Purpose:
    This script creates a table in the 'silver' schema, dropping existing table 
    if they already exist.
	  Run this script to re-define the DDL structure of 'bronze' Table
===============================================================================
*/

DROP TABLE IF EXISTS silver_jobs CASCADE;

CREATE TABLE silver_jobs (

    job_key BIGSERIAL PRIMARY KEY,

    source TEXT NOT NULL,
    job_id TEXT NOT NULL,

    search_term TEXT,
    url TEXT,
    collection_timestamp TIMESTAMP,

    job_title_raw TEXT,
    job_title_standardized TEXT,

    company TEXT,
    location TEXT,
    duplicate_status TEXT,
    employment_type TEXT,
    department TEXT,

    salary_min INTEGER,
    salary_max INTEGER,
    
    posting_date DATE,
    job_description TEXT

    CONSTRAINT uq_silver_source_job
        UNIQUE (source, job_id)

);

DROP TABLE IF EXISTS ai_enrichment;

CREATE TABLE ai_enrichment (

    enrichment_id BIGSERIAL PRIMARY KEY,

    job_key BIGINT NOT NULL,

    skills JSONB,
    requirements JSONB,

    ai_model TEXT,
    ai_prompt_version TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ai_enrichment_job_key
        FOREIGN KEY (job_key)
        REFERENCES silver_jobs(job_key)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);