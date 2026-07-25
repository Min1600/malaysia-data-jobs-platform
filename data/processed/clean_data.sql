/*
standardize job title, employment type, location, company (department still figuring out how to standardize)
salary min and max format is edited to ensure able to become INT type 
flag potential duplicate jobs
*/

WITH standardized_jobs AS (

    SELECT
        source,
        job_id,
        search_term,
        url,
        collection_timestamp,
        job_title AS job_title_raw,
        -- standardize job_title
        CASE
            WHEN job_title ILIKE '%Data Analyst%' THEN 'Data Analyst'
            WHEN job_title ILIKE '%Data Analytic%' THEN 'Data Analyst'
            WHEN job_title ILIKE '%Data Engineer%' THEN 'Data Engineer'
            WHEN job_title ILIKE '%Data Scientist%' THEN 'Data Scientist'
            WHEN job_title ILIKE '%Data Science%' THEN 'Data Scientist'
            WHEN job_title ILIKE '%AI Engineer%' THEN 'AI Engineer'
            WHEN job_title ILIKE '%Machine Learning Engineer%' THEN 'ML Engineer'
            WHEN job_title ILIKE '%ML Engineer%' THEN 'ML Engineer'
            WHEN job_title ILIKE '%data warehouse developer%' THEN 'Data Warehouse Developer'
            WHEN job_title ILIKE '%database administrator%' THEN 'Database Administrator'
            WHEN job_title ILIKE '%finance analyst%' THEN 'Finance Analyst'
            WHEN job_title ILIKE '%business intelligence analyst%' THEN 'BI Analyst'
            WHEN job_title ILIKE '%bi analyst%' THEN 'BI Analyst'
            WHEN job_title ILIKE '%bi developer%' THEN 'BI Developer'
            WHEN job_title ILIKE '%business analyst%' THEN 'Business Analyst'
            WHEN job_title ILIKE '%analytics engineer%'THEN 'Analytics Engineer'
            ELSE job_title
        END AS job_title_standardized,
        -- standardize company names
        CASE 
            WHEN company ILIKE '%pwc%' THEN 'PwC Malaysia'
            WHEN company ILIKE '%hong leong%' THEN 'Hong Leong'
            WHEN company ILIKE '%luxoft%' THEN 'Luxoft'
            WHEN company ILIKE '%accenture%' THEN 'Accenture'
            WHEN company ILIKE '%shopee%' THEN 'Shopee'
            WHEN company ILIKE '%uob%' THEN 'UOB'
            WHEN company ILIKE '%maybank%' THEN 'Maybank'
            WHEN company ILIKE '%aia%' THEN 'AIA'
            WHEN company ILIKE '%ocbc%' THEN 'OCBC'
            WHEN company ILIKE '%alliance bank%' THEN 'Alliance Bank'
            WHEN company ILIKE '%deloitte%' THEN 'Deloitte'
            ELSE company
        END AS company,
        -- standardize locations
        CASE
            WHEN location ILIKE '%kuala lumpur%' THEN 'Kuala Lumpur'
            ELSE split_part(location, ',', 1)
        END AS location,
        -- standardize employement type 
        CASE
            WHEN job_title ILIKE '%intern%' THEN 'Internship'
            WHEN employment_type ILIKE '%full%time%' THEN 'Full-time'
            WHEN employment_type ILIKE '%part%time%' THEN 'Part-time'
            WHEN employment_type ILIKE '%contract%' THEN 'Contract'
            ELSE employment_type
        END AS employment_type,
        -- no changes for now to department
        department,
        -- edit salary min to reflect correctly
        CAST(
            CASE 
                WHEN salary_min LIKE 'RM%–%per month' 
                THEN NULLIF(TRIM(REPLACE(REPLACE(RIGHT(split_part(salary_min, '–', 1), -3), ',', ''), chr(160), '')), '')
                ELSE NULL 
            END AS INTEGER
        ) AS salary_min,
        -- edit salary max to reflect correctly
        CAST(
            CASE 
                WHEN salary_max LIKE 'RM%–%per month' 
                THEN NULLIF(TRIM(REPLACE(REPLACE(LEFT(RIGHT(split_part(salary_max, '–', -1), -3), -10), ',', ''), chr(160), '')), '')
                ELSE NULL 
            END AS INTEGER
        ) AS salary_max,
        CAST(posting_date AS DATE),
        job_description
    FROM stg_jobs
)

INSERT INTO silver_jobs (

    source,
    job_id,
    search_term,
    url,
    collection_timestamp,
    job_title_raw,
    job_title_standardized,
    company,
    location,
    duplicate_status,
    employment_type,
    department,
    salary_min,
    salary_max,
    posting_date,
    job_description

)

SELECT
    source,
    job_id,
    search_term,
    url,
    collection_timestamp,
    job_title_raw,
    job_title_standardized,
    company,
    location,
    CASE
        -- Same source, same standardized job details
        WHEN COUNT(*) OVER (
            PARTITION BY
                source,
                company,
                job_title_raw,
                location
        ) > 1
        THEN 'Potential Duplicate'
        -- Same job characteristics, but listed on different websites
        WHEN COUNT(*) OVER (
            PARTITION BY
                company,
                job_title_raw,
                location
        ) > 1
        THEN 'Cross-source Match'
        ELSE 'Unique'
    END AS duplicate_status,
    employment_type,
    department,
    salary_min,
    salary_max,
    posting_date,
    job_description

FROM standardized_jobs;
ON CONFLICT 
DO NOTHING;



