/*
===============================================================================
DDL Script: Create Bronze Table
===============================================================================
Script Purpose:
    This script create a table in the 'bronze' schema, dropping existing table
    if they already exist.
	  Run this script to re-define the DDL structure of 'bronze' Table
===============================================================================
*/

DROP TABLE IF EXISTS stg_jobs;

CREATE TABLE stg_jobs (
    -- Unique identifier
    source TEXT NOT NULL,
    job_id TEXT NOT NULL,

    -- Metadata
    search_term TEXT NOT NULL,
    url TEXT NOT NULL,
    collection_timestamp TIMESTAMP NOT NULL,

    -- Job details
    job_title TEXT,
    company TEXT,
    location TEXT,
    employment_type TEXT,
    department TEXT,

    -- Salary
    salary_min TEXT,
    salary_max TEXT,

    -- Posting information
    posting_date TEXT,

    -- Content
    job_description TEXT,
    requirements TEXT,
    skills JSONB,
    raw_html TEXT,

    -- Prevent duplicate jobs from the same source
    PRIMARY KEY (source, job_id)
);